#! /usr/bin/env python

from distutils.core import setup

requirements = [
    'numpy',
    'pandas',
    'pysal'
]

setup(
    name='riverkit',
    version='0.1',
    description='River data analysis kit.',
    author='Will Dicharry',
    author_email='wdicharry@gmail.com',
    install_requires=requirements
)
