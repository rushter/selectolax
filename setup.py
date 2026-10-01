#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import platform
import logging

import sys
from setuptools import setup, find_packages, Extension


logging.basicConfig(level=logging.INFO)

with io.open("README.md", mode="rt", encoding="utf-8") as readme_file:
    readme = readme_file.read()

# Setup flags
USE_STATIC = False
USE_CYTHON = False
PLATFORM = "windows_nt" if platform.system() == "Windows" else "posix"
INCLUDE_LEXBOR = bool(os.environ.get("USE_LEXBOR", True))

ARCH = platform.architecture()[0]

try:
    from Cython.Build import cythonize

    HAS_CYTHON = True
    USE_CYTHON = True
except ImportError as err:
    HAS_CYTHON = False

if "--static" in sys.argv:
    USE_STATIC = True
    sys.argv.remove("--static")

if "--lexbor" in sys.argv:
    INCLUDE_LEXBOR = True
    sys.argv.remove("--lexbor")

if "--cython" in sys.argv:
    if HAS_CYTHON:
        USE_CYTHON = True
    else:
        raise ImportError("No module named 'Cython'")
    sys.argv.remove("--cython")

# If there are no pretranspiled source files
if HAS_CYTHON and not os.path.exists("selectolax/lexbor.c"):
    USE_CYTHON = True

COMPILER_DIRECTIVES = {
    "language_level": 3,
    "embedsignature": True,
    "annotation_typing": False,
    "emit_code_comments": True,
    "boundscheck": False,
    "wraparound": False,
    "freethreading_compatible": "True",
    "subinterpreters_compatible": "own_gil",
}


def find_lexbor_files(lexbor_path="lexbor/source"):
    c_files = []
    if os.path.exists(lexbor_path):
        for root, dirs, files in os.walk(lexbor_path):
            for file in files:
                if file.endswith(".c"):
                    file_path = os.path.join(root, file)

                    # Filter platform specific files
                    if (file_path.find("ports") >= 0) and (
                        not file_path.find(PLATFORM) >= 0
                    ):
                        continue
                    c_files.append(file_path)
    return c_files


def make_extensions():
    logging.info(f"USE_CYTHON: {USE_CYTHON}")
    logging.info(f"INCLUDE_LEXBOR: {INCLUDE_LEXBOR}")
    logging.info(f"USE_STATIC: {USE_STATIC}")

    files_to_compile_lxb = []
    extra_objects_lxb = []

    if USE_CYTHON:
        if INCLUDE_LEXBOR:
            files_to_compile_lxb = [
                "selectolax/lexbor.pyx",
            ]
    else:
        if INCLUDE_LEXBOR:
            files_to_compile_lxb = [
                "selectolax/lexbor.c",
            ]

    if USE_STATIC:
        if INCLUDE_LEXBOR:
            extra_objects_lxb = ["lexbor/liblexbor_static.a"]
    else:
        if INCLUDE_LEXBOR:
            files_to_compile_lxb.extend(find_lexbor_files("lexbor/source"))

    compile_arguments_lxb = [
        "-DLEXBOR_STATIC",
    ]
    link_arguments_lxb = []

    if PLATFORM == "posix":
        args = [
            "-pedantic",
            "-fPIC",
            # Required for --gc-sections to collect anything: LEXBOR_STATIC
            # expands LXB_API to nothing, so every lexbor symbol would
            # otherwise get default visibility and be treated as reachable
            # from outside the shared object. The linker must then keep it
            # along with any table it references, and none of the unused
            # encoding/unicode/CSS-serialization tables can be dropped.
            "-fvisibility=hidden",
            "-fvisibility-inlines-hidden",
            "-ffunction-sections",
            "-fdata-sections",
            "-Wno-unused-variable",
            "-Wno-unused-function",
            "-std=c99",
            "-O2",
            "-g0",
        ]
        compile_arguments_lxb.extend(args)
        # The per-section compile flags above are only useful if the linker is
        # allowed to drop unreferenced ones. Without this, lexbor's encoding
        # resolution tables (encodings selectolax never uses) stay linked in.
        # The flag name is linker-specific, so it cannot be shared.
        if platform.system() == "Darwin":
            link_arguments_lxb.append("-Wl,-dead_strip")
        else:
            link_arguments_lxb.append("-Wl,--gc-sections")

    elif PLATFORM == "windows_nt":
        compile_arguments_lxb.extend(
            [
                "-D_WIN64" if ARCH == "64bit" else "-D_WIN32",
                "/O2",
                "/Gy",
                "/OPT:REF",
                "/OPT:ICF",
            ]
        )

    extensions = []

    if INCLUDE_LEXBOR:
        extensions.append(
            Extension(
                "selectolax.lexbor",
                files_to_compile_lxb,
                language="c",
                include_dirs=[
                    "lexbor/source/",
                ],
                extra_objects=extra_objects_lxb,
                extra_compile_args=compile_arguments_lxb,
                extra_link_args=link_arguments_lxb,
            )
        )
    if USE_CYTHON:
        extensions = cythonize(extensions, compiler_directives=COMPILER_DIRECTIVES)

    return extensions


setup(
    name="selectolax",
    version="0.4.13",
    description="A fast HTML5 parser with CSS selectors, written in Cython, using the Lexbor engine.",
    long_description=readme,
    author="Artem Golubin",
    author_email="me@rushter.com",
    url="https://github.com/rushter/selectolax",
    packages=find_packages(include=["selectolax"]),
    package_data={"selectolax": ["py.typed"]},
    include_package_data=True,
    zip_safe=False,
    ext_modules=make_extensions(),
)
