#! /usr/bin/env python

from setuptools import setup

requirements = [
    'setuptools',
    'numpy',
    'pandas',
    'pysal',
    'scipy'
]

setup(
    name='waterkit',
    version='0.1',
    description='Water data analysis kit.',
    author='Will Dicharry',
    author_email='wdicharry@gmail.com',
    install_requires=requirements,
    test_suite="tests"
)
