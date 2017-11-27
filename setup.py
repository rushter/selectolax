#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

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


def find_c_files(modest_path="modest/source"):
    # todo: refactor
    c_files = ["selectolax/*.pyx",
               "selectolax/helper.c",

               ]
    if os.path.exists(modest_path):
        for root, dirs, files in os.walk(modest_path):
            for file in files:
                if file.endswith(".c"):
                    file_path = os.path.join(root, file)

                    # todo: make it work on Windows
                    if file_path.find('windows') >= 0:
                        continue

                    c_files.append(file_path)
    return c_files


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
    ext_modules=cythonize([Extension("selectolax.parser",
                                     find_c_files(),
                                     include_dirs=[
                                         'modest/source/'
                                     ],
                                     )]),
)
