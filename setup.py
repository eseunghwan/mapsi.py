#!/usr/bin/env python

"""The setup script."""

from setuptools import setup
from mapsi import __author__, __email__, __version__

with open("requirements.txt", "r", encoding = "utf-8") as require_read:
    requires = require_read.readlines()

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

setup(
    author=__author__,
    author_email=__email__,
    version=__version__,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Korean",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    name="mapsipy",
    description="MVVM UI Framework for Python and Brython",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    license="MIT license",
    keywords=["mapsipy", "brython", "mvvm"],
    entry_points={
        "console_scripts": [
            "mapsipy-cli=mapsi.cli:main",
        ],
    },
    include_package_data=False,
    install_requires=requires,
    setup_requires=requires,
    packages=["mapsi", "mapsi/assets", "mapsi/build_files", "mapsi/template_files"],
    package_data={
        "": [
            "**/*.*",
            "**/**/*.*",
            "**/**/**/*.*",
            "**/**/**/**/*.*",
            "**/**/**/**/**/*.*"
        ]
    },
    url="https://github.com/eseunghwan/mapsipy",
    zip_safe=False
)
