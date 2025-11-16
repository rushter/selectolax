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
INCLUDE_MODEST = bool(os.environ.get("USE_MODEST", True))

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

if "--disable-modest" in sys.argv:
    INCLUDE_MODEST = False
    sys.argv.remove("--disable-modest")

if "--cython" in sys.argv:
    if HAS_CYTHON:
        USE_CYTHON = True
    else:
        raise ImportError("No module named 'Cython'")
    sys.argv.remove("--cython")

# If there are no pretranspiled source files
if HAS_CYTHON and not os.path.exists("selectolax/parser.c"):
    USE_CYTHON = True

COMPILER_DIRECTIVES = {
    "language_level": 3,
    "embedsignature": True,
    "annotation_typing": False,
    "emit_code_comments": True,
    "boundscheck": False,
    "wraparound": False,
}


def find_modest_files(modest_path="modest/source"):
    c_files = []
    if os.path.exists(modest_path):
        for root, dirs, files in os.walk(modest_path):
            for file in files:
                if file.endswith(".c"):
                    file_path = os.path.join(root, file)

                    # Filter platform specific files
                    if (file_path.find("myport") >= 0) and (
                        not file_path.find(PLATFORM) >= 0
                    ):
                        continue

                    if INCLUDE_LEXBOR:
                        if (file_path.find("ports") >= 0) and (
                            not file_path.find(PLATFORM) >= 0
                        ):
                            continue
                    c_files.append(file_path)
    return c_files


def make_extensions():
    logging.info(f"USE_CYTHON: {USE_CYTHON}")
    logging.info(f"INCLUDE_LEXBOR: {INCLUDE_LEXBOR}")
    logging.info(f"INCLUDE_MODEST: {INCLUDE_MODEST}")
    logging.info(f"USE_STATIC: {USE_STATIC}")

    files_to_compile_lxb = []
    files_to_compile = []
    extra_objects_lxb, extra_objects = [], []

    if USE_CYTHON:
        if INCLUDE_MODEST:
            files_to_compile = [
                "selectolax/parser.pyx",
            ]
        if INCLUDE_LEXBOR:
            files_to_compile_lxb = [
                "selectolax/lexbor.pyx",
            ]
    else:
        if INCLUDE_MODEST:
            files_to_compile = ["selectolax/parser.c"]
        if INCLUDE_LEXBOR:
            files_to_compile_lxb = [
                "selectolax/lexbor.c",
            ]

    if USE_STATIC:
        if INCLUDE_MODEST:
            extra_objects = ["modest/lib/libmodest_static.a"]
        if INCLUDE_LEXBOR:
            extra_objects_lxb = ["lexbor/liblexbor_static.a"]
    else:
        if INCLUDE_MODEST:
            files_to_compile.extend(find_modest_files("modest/source"))
        if INCLUDE_LEXBOR:
            files_to_compile_lxb.extend(find_modest_files("lexbor/source"))

    compile_arguments_lxb = [
        "-DLEXBOR_STATIC",
    ]
    compile_arguments = [
        "-DMODEST_BUILD_OS=%s" % platform.system(),
        "-DMyCORE_OS_%s" % platform.system(),
        "-DMODEST_PORT_NAME=%s" % PLATFORM,
        "-DMyCORE_BUILD_WITHOUT_THREADS=YES",
        "-DMyCORE_BUILD_DEBUG=NO",
    ]

    if PLATFORM == "posix":
        args = [
            "-pedantic",
            "-fPIC",
            "-Wno-unused-variable",
            "-Wno-unused-function",
            "-std=c99",
            "-O2",
            "-g0",
        ]
        compile_arguments.extend(args)
        compile_arguments_lxb.extend(args)
    elif PLATFORM == "windows_nt":
        compile_arguments_lxb.extend(
            [
                "-D_WIN64" if ARCH == "64bit" else "-D_WIN32",
            ]
        )

    extensions = []
    if INCLUDE_MODEST:
        extensions.append(
            Extension(
                "selectolax.parser",
                files_to_compile,
                language="c",
                include_dirs=[
                    "modest/include/",
                ],
                extra_objects=extra_objects,
                extra_compile_args=compile_arguments,
            )
        )

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
            )
        )
    if USE_CYTHON:
        extensions = cythonize(extensions, compiler_directives=COMPILER_DIRECTIVES)

    return extensions


setup(
    name="selectolax",
    version="0.4.2",
    description="Fast HTML5 parser with CSS selectors.",
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
