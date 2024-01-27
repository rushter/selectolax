MAX_HTML_INPUT_SIZE = 250e+7

def preprocess_input(html, decode_errors='ignore'):
    if isinstance(html, (str, unicode)):
        bytes_html = html.encode('UTF-8', errors=decode_errors)
    elif isinstance(html, bytes):
        bytes_html = html
    else:
        raise TypeError("Expected a string, but %s found" % type(html).__name__)
    html_len = len(bytes_html)
    if html_len > MAX_HTML_INPUT_SIZE:
        raise ValueError("The specified HTML input is too large to be processed (%d bytes)" % html_len)
    return bytes_html, html_len
