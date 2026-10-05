#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import platform
import logging

import sys
from concurrent.futures import ThreadPoolExecutor

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as _build_ext


logging.basicConfig(level=logging.INFO)

with io.open("README.md", mode="rt", encoding="utf-8") as readme_file:
    readme = readme_file.read()

# Setup flags
USE_STATIC = False
USE_CYTHON = False
PLATFORM = "windows_nt" if platform.system() == "Windows" else "posix"

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
    logging.info(f"USE_STATIC: {USE_STATIC}")

    if USE_CYTHON:
        files_to_compile_lxb = [
            "selectolax/lexbor.pyx",
        ]
    else:
        files_to_compile_lxb = [
            "selectolax/lexbor.c",
        ]

    extra_objects_lxb = []

    if USE_STATIC:
        extra_objects_lxb = ["lexbor/liblexbor_static.a"]
    else:
        files_to_compile_lxb.extend(find_lexbor_files("lexbor/source"))

    compile_arguments_lxb = [
        "-DLEXBOR_STATIC",
    ]

    if PLATFORM == "posix":
        args = [
            "-pedantic",
            "-fPIC",
            "-Wno-unused-variable",
            "-Wno-unused-function",
            "-Wno-overlength-strings",
            "-std=c99",
            "-O3",
            "-g0",
        ]
        compile_arguments_lxb.extend(args)
    elif PLATFORM == "windows_nt":
        compile_arguments_lxb.extend(
            [
                "-D_WIN64" if ARCH == "64bit" else "-D_WIN32",
            ]
        )

    extensions = []
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


class build_ext_parallel(_build_ext):
    """Compile the sources of an extension concurrently.

    distutils walks its sources in a serial loop, and ``build_ext --parallel``
    only parallelises the outer per-extension loop, so a single extension built
    from 200+ files still gets one worker. ``_compile()`` is the documented
    per-file hook and just spawns a subprocess, so it is safe to dispatch
    through a thread pool.

    Set BUILD_JOBS to a worker count, or to "auto" for os.cpu_count().
    Unset means serial.
    """

    def build_extensions(self):
        workers = os.environ.get("BUILD_JOBS", "1")
        workers = (os.cpu_count() or 1) if workers == "auto" else int(workers)
        compiler = self.compiler
        if workers <= 1:
            super().build_extensions()
            return

        original_compile, original_inner = compiler.compile, compiler._compile
        futures = []
        pool = ThreadPoolExecutor(max_workers=workers)

        def inner(*args):
            futures.append(pool.submit(original_inner, *args))

        def compile(*args, **kwargs):
            try:
                return original_compile(*args, **kwargs)
            finally:
                for future in futures:
                    future.result()

        compiler._compile, compiler.compile = inner, compile
        try:
            super().build_extensions()
        finally:
            compiler.compile, compiler._compile = original_compile, original_inner
            pool.shutdown()


setup(
    name="selectolax",
    version="1.0.0",
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
    cmdclass={"build_ext": build_ext_parallel},
)
