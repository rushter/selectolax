#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import platform

import sys
from Cython.Build import cythonize
from setuptools import setup, find_packages, Extension

with open('README.MD') as readme_file:
    readme = readme_file.read()

requirements = [
    'cython',

]

setup_requirements = [
    'pytest-runner',

]

test_requirements = [
    'pytest',
]

# Setup flags
myport_platform = 'windows_nt' if platform.system() == 'Windows' else 'posix'

if "--static" in sys.argv:
    is_static = True
    sys.argv.remove("--static")
else:
    is_static = False


def find_modest_files(modest_path="modest/source"):
    c_files = []
    if os.path.exists(modest_path):
        for root, dirs, files in os.walk(modest_path):
            for file in files:
                if file.endswith(".c"):
                    file_path = os.path.join(root, file)

                    # Filter platform specific files
                    if (file_path.find('myport') >= 0) and (not file_path.find(myport_platform) >= 0):
                        continue

                    c_files.append(file_path)
    return c_files


def make_extension(static=False):
    files_to_compile = ["selectolax/parser.pyx"]
    if not static:
        files_to_compile.extend(find_modest_files())

    if static:
        extra_objects = ["modest/lib/libmodest_static.a"]
    else:
        extra_objects = []

    extension = Extension("selectolax.parser",
                          files_to_compile,
                          language='c',
                          include_dirs=['modest/include/', ],
                          extra_objects=extra_objects,
                          extra_compile_args=[
                              "-pedantic", "-fPIC",
                              "-DMODEST_BUILD_OS=%s" % platform.system(),
                              "-DMyCORE_OS_%s" % platform.system(),
                              "-DMODEST_PORT_NAME=posix",
                              "-DMyCORE_BUILD_WITHOUT_THREADS=YES",
                              "-DMyCORE_BUILD_DEBUG=NO",
                              "-O2", "-Wno-unused-variable",
                              "-Wno-unused-function",
                              "-std=c99"
                          ]
                          )
    return extension


setup(
    name='selectolax',
    version='0.1.0',
    description="Fast HTML5 CSS selector.",
    long_description=readme,
    author="Artem Golubin",
    author_email='me@rushter.com',
    url='https://github.com/rushter/selectolax',
    packages=find_packages(include=['selectolax']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='selectolax',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    # test_suite='tests',
    # tests_require=test_requirements,
    ext_modules=cythonize(([make_extension(is_static)])),
)
