#!/usr/bin/env python
# coding=utf-8

import os
from distutils.core import setup

delattr(os, 'link')

setup(
    name='fairshare',
    version='1.0',
    author='Jerome Belleman',
    author_email='Jerome.Belleman@gmail.com',
    url='http://cern.ch/jbl',
    description="Query LSF fairshare information",
    long_description="Collect and query LSF fairshare information",
    packages=['fairshare'],
    scripts=['scripts/fairshare'],
    data_files=[('/usr/share/man/man1', ['fairshare.1'])],
)
