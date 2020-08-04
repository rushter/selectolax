#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import platform

import sys
from setuptools import setup, find_packages, Extension

with io.open('README.rst', mode='rt', encoding='utf-8') as readme_file:
    readme = readme_file.read()

# Setup flags
USE_STATIC = False
USE_CYTHON = False
PLATFORM = 'windows_nt' if platform.system() == 'Windows' else 'posix'

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
if HAS_CYTHON and not os.path.exists("selectolax/parser.c"):
    USE_CYTHON = True


def find_modest_files(modest_path="modest/source"):
    c_files = []
    if os.path.exists(modest_path):
        for root, dirs, files in os.walk(modest_path):
            for file in files:
                if file.endswith(".c"):
                    file_path = os.path.join(root, file)

                    # Filter platform specific files
                    if (file_path.find('myport') >= 0) and (not file_path.find(PLATFORM) >= 0):
                        continue

                    c_files.append(file_path)
    return c_files


def make_extensions():
    if USE_CYTHON:
        files_to_compile = ["selectolax/parser.pyx"]
    else:
        files_to_compile = ["selectolax/parser.c"]

    if USE_STATIC:
        extra_objects = ["modest/lib/libmodest_static.a"]
    else:
        files_to_compile.extend(find_modest_files())
        extra_objects = []

    compile_arguments = [
        "-DMODEST_BUILD_OS=%s" % platform.system(),
        "-DMyCORE_OS_%s" % platform.system(),
        "-DMODEST_PORT_NAME=%s" % PLATFORM,
        "-DMyCORE_BUILD_WITHOUT_THREADS=YES",
        "-DMyCORE_BUILD_DEBUG=NO",
        "-O2",

    ]

    if PLATFORM == 'posix':
        compile_arguments.extend([
            "-pedantic", "-fPIC",
            "-Wno-unused-variable",
            "-Wno-unused-function",
            "-std=c99"

        ])

    extension = Extension("selectolax.parser",
                          files_to_compile,
                          language='c',
                          include_dirs=['modest/include/', ],
                          extra_objects=extra_objects,
                          extra_compile_args=compile_arguments,
                          )

    extensions = ([extension, ])

    if USE_CYTHON:
        extensions = cythonize(extensions)

    return extensions


setup(
    name='selectolax',
    version='0.2.6',
    description="Fast HTML5 parser with CSS selectors.",
    long_description=readme,
    author="Artem Golubin",
    author_email='me@rushter.com',
    url='https://github.com/rushter/selectolax',
    packages=find_packages(include=['selectolax']),
    include_package_data=True,
    install_requires=[],
    license="MIT license",
    zip_safe=False,
    keywords='selectolax',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=[
        'pytest',
    ],
    ext_modules=make_extensions(),
)
