import codecs

# 2500 MB
MAX_HTML_INPUT_SIZE = 2_500_000_000

# The HTML Standard only looks for a <meta> encoding declaration within the
# first 1024 bytes of a byte stream.
_MAX_ENCODING_PRESCAN_SIZE = 1024

# How much input is decoded per step when transcoding. Transcoding walks the
# whole document, and `MAX_HTML_INPUT_SIZE` allows for very large ones, so the
# work is done in slices to keep the extra memory close to a single slice.
_TRANSCODE_CHUNK_SIZE = 1_048_576

_BOM_UTF8 = b'\xef\xbb\xbf'
_BOM_UTF16_BE = b'\xfe\xff'
_BOM_UTF16_LE = b'\xff\xfe'

# Byte-order marks keyed by the codec they announce. A codec that is not a key
# here never has a mark to skip.
_BOMS_BY_CODEC = {
    'utf-8': _BOM_UTF8,
    'utf-16-be': _BOM_UTF16_BE,
    'utf-16-le': _BOM_UTF16_LE,
}

# Labels the HTML Standard resolves to an encoding Python's codec registry does
# not know under that name. `replacement` maps to `ascii` deliberately: with
# `errors='replace'` that turns every non-ASCII byte into U+FFFD and leaves the
# rest alone, which is what the standard's "replacement" encoding prescribes.
_CODEC_ALIASES = {
    'iso-8859-8-i': 'iso-8859-8',
    'replacement': 'ascii',
    'x-mac-cyrillic': 'mac_cyrillic',
}


def _prescan_encoding_label(bytes html_bytes):
    """Return the encoding label declared at the start of a byte stream, if any.

    Delegates to lexbor's ``lxb_html_encoding_prescan()``, an implementation of
    the HTML Standard's "prescan a byte stream to determine its encoding" step.
    It recognises both ``<meta charset>`` and
    ``<meta http-equiv="content-type" content="...charset=...">``, and it
    already applies the standard's label aliasing, so a ``utf-16*`` label comes
    back as ``UTF-8`` and ``x-user-defined`` as ``windows-1252``.

    Only the first ``_MAX_ENCODING_PRESCAN_SIZE`` bytes are looked at. Lexbor
    scans as far as it is allowed to, and the standard is what draws the line at
    1024 bytes: honouring a declaration found further into the document would
    let page content decide the encoding it is decoded with.

    Parameters
    ----------
    html_bytes : bytes
        Raw HTML to scan.

    Returns
    -------
    bytes or None
        The declared label, or ``None`` when the stream declares nothing.

    Raises
    ------
    MemoryError
        If the prescan object cannot be allocated.
    """
    cdef lxb_html_encoding_t* encoding
    cdef const lxb_char_t* data
    cdef const lxb_char_t* label
    cdef size_t label_len = 0
    cdef size_t scan_len = min(len(html_bytes), _MAX_ENCODING_PRESCAN_SIZE)

    data = <const lxb_char_t *> PyBytes_AS_STRING(html_bytes)

    encoding = lxb_html_encoding_create()
    if encoding == NULL:
        raise MemoryError("Can't allocate memory for the encoding prescan.")

    try:
        with nogil:
            label = lxb_html_encoding_prescan(encoding, data,
                                              data + scan_len, &label_len)

        if label == NULL:
            return None

        return PyBytes_FromStringAndSize(<const char *> label, label_len)
    finally:
        lxb_html_encoding_destroy(encoding, True)


def _text_codec_name(str name):
    """Return ``name`` when bytes can be decoded with it, ``None`` otherwise.

    ``codecs`` also holds transforms that are not encodings, such as the binary
    ``base64`` and the text transform ``rot13``. A document can name one in
    ``<meta charset>``, so such a label has to be rejected like an unknown one
    rather than raise from inside the codec module. The registry flags those with
    ``_is_text_encoding``; decoding a few bytes of markup catches the rest, which
    claim to be text encodings but refuse to be given bytes. The probe asks for
    ``errors='replace'`` because that is what transcoding uses, and some codecs
    accept only some of the error handlers.
    """
    if not name:
        return None

    try:
        codec_info = codecs.lookup(name)
    except (LookupError, ValueError):
        return None

    if not getattr(codec_info, '_is_text_encoding', False):
        return None

    try:
        b'<meta>'.decode(name, 'replace')
    except Exception:
        return None

    return name


def _encoding_codec(bytes html_bytes):
    """Return the name of the codec a byte stream should be decoded with.

    Follows the HTML Standard's order of preference: a byte-order mark wins over
    any ``<meta>`` declaration, then the declaration is used, and a stream that
    declares nothing is decoded as UTF-8.

    UTF-8 is that last fallback rather than the standard's windows-1252 because
    every other selectolax code path already assumes UTF-8, and switching the
    default here would reinterpret input that used to parse correctly. A label
    that is unknown, or that names something bytes cannot be decoded with, falls
    back the same way.

    Parameters
    ----------
    html_bytes : bytes
        Raw HTML to inspect.

    Returns
    -------
    str
        Name of a codec known to Python's codec registry that decodes bytes.
    """
    if html_bytes.startswith(_BOM_UTF8):
        return 'utf-8'
    if html_bytes.startswith(_BOM_UTF16_LE):
        return 'utf-16-le'
    if html_bytes.startswith(_BOM_UTF16_BE):
        return 'utf-16-be'

    label = _prescan_encoding_label(html_bytes)
    if label is None:
        return 'utf-8'

    name = label.decode('ascii', errors='replace').strip().lower()
    codec = _text_codec_name(_CODEC_ALIASES.get(name, name))
    if codec is None:
        # An unknown or malformed label is not worth failing a parse over.
        # The standard prescribes treating it as UTF-8.
        return 'utf-8'

    return codec


def _transcode_to_utf8(bytes html_bytes, str codec):
    """Decode a byte stream with ``codec`` and return the text as UTF-8 bytes.

    Bytes that do not form a valid sequence in the source encoding become
    U+FFFD, as the HTML Standard prescribes, instead of being dropped or kept
    as-is to blow up on the way out of the parser.

    Parameters
    ----------
    html_bytes : bytes
        Raw HTML to transcode.
    codec : str
        Name of the codec to decode with.

    Returns
    -------
    bytes
        The decoded document, encoded as UTF-8.

    Raises
    ------
    ValueError
        If the transcoded document exceeds ``MAX_HTML_INPUT_SIZE``.
    """
    cdef bytearray out

    try:
        decoder = codecs.getincrementaldecoder(codec)(errors='replace')
    except LookupError:
        # A codec without an incremental decoder has to be handed all at once.
        out = bytearray(html_bytes.decode(codec, 'replace').encode('UTF-8'))
        _check_input_size(len(out))
        return bytes(out)

    out = bytearray()
    for start in range(0, len(html_bytes), _TRANSCODE_CHUNK_SIZE):
        out += decoder.decode(
            html_bytes[start:start + _TRANSCODE_CHUNK_SIZE]
        ).encode('UTF-8')
        _check_input_size(len(out))

    out += decoder.decode(b'', True).encode('UTF-8')
    _check_input_size(len(out))

    return bytes(out)


def _decode_to_utf8(bytes html_bytes):
    """Return a byte stream as UTF-8, using the encoding it declares.

    Parameters
    ----------
    html_bytes : bytes
        Raw HTML to decode.

    Returns
    -------
    bytes
        The document as UTF-8, without a leading byte-order mark. Streams that
        are already UTF-8 are returned unchanged, apart from that mark.
    """
    codec = _encoding_codec(html_bytes)

    bom = _BOMS_BY_CODEC.get(codec)
    if bom is not None and html_bytes.startswith(bom):
        html_bytes = html_bytes[len(bom):]

    if codec == 'utf-8':
        return html_bytes

    return _transcode_to_utf8(html_bytes, codec)


def _check_input_size(html_len):
    """Reject an input that is too large to be processed.

    Parameters
    ----------
    html_len : int
        Size of the input in bytes.

    Raises
    ------
    ValueError
        If the input exceeds ``MAX_HTML_INPUT_SIZE``.
    """
    if html_len > MAX_HTML_INPUT_SIZE:
        raise ValueError("The specified HTML input is too large to be processed (%d bytes)" % html_len)


def preprocess_input(html, decode_errors='ignore', encoding=False):
    """Normalise parser input into the UTF-8 bytes lexbor is fed with.

    Parameters
    ----------
    html : str or bytes
        Content to parse.
    decode_errors : str, default 'ignore'
        Passed to ``str.encode`` when ``html`` is text.
    encoding : bool, default False
        When ``True`` and ``html`` is bytes, detect the encoding the document
        declares and transcode it to UTF-8 first, so that ``<meta charset>`` and
        a leading byte-order mark are honoured. Text input needs none of this
        and is unaffected.

    Returns
    -------
    tuple of (bytes, int)
        The UTF-8 bytes to parse and their length.

    Raises
    ------
    TypeError
        If ``html`` is neither text nor bytes.
    ValueError
        If the input, or its transcoded form, exceeds ``MAX_HTML_INPUT_SIZE``.
    """
    if isinstance(html, (str, unicode)):
        bytes_html = html.encode('UTF-8', errors=decode_errors)
    elif isinstance(html, bytes):
        bytes_html = _decode_to_utf8(html) if encoding and html else html
    else:
        raise TypeError("Expected a string, but %s found" % type(html).__name__)
    html_len = len(bytes_html)
    _check_input_size(html_len)
    return bytes_html, html_len
