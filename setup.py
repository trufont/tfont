#!/usr/bin/env python
from setuptools import setup, find_packages


with open('README.rst', 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tfont",
    use_scm_version={"write_to": "src/tfont/_version.py"},
    description="tfont is a font library that writes to JSON.",
    long_description=long_description,
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="https://github.com/trufont/tfont",
    license="Apache 2.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "fonttools>=3.24.0",
        "python-rapidjson>=0.5.0",
        "attrs>=17.3.0",
        "cattrs>=0.8.0",
    ],
    extras_require={
        "ufo": [
            "ufoLib2>=0.1.3",
        ],
        "testing": [
            "pytest",
            "pytest-cov",
            "pytest-randomly",
        ],
    },
    setup_requires=[
        "setuptools_scm",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: Fonts",
        "License :: OSI Approved :: Apache Software License",
    ],
)
