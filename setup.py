#!/usr/bin/env python

import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


# wui_requires = ['bokeh']
wui_requires = []

setup(
    name="fpvgcc",
    version="0.9.0",
    author="Chintalagiri Shashank",
    author_email="shashank@chintal.in",
    description="Analysing code footprint on embedded microcontrollers "
                "using GCC generated Map files",
    license="GPLv3+",
    keywords="utilities",
    url="https://github.com/chintal/fpv-gcc",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Environment :: Console"
    ],
    install_requires=[
        'six',
        'wheel',
        'prettytable',
    ],
    extras_require={
        'docs': ['sphinx', 'sphinx-argparse'],
        'wui': wui_requires,
    },
    platforms='any',
    entry_points={
        'console_scripts': ['fpvgcc=fpvgcc.cli:main'],
    }
)
