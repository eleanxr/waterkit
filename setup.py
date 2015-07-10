#! /usr/bin/env python

from setuptools import setup

requirements = [
    'setuptools',
    # Choose numpy for ArcGIS 10.2
    'numpy==1.7.1',
    # Choose pandas for numpy 1.7.1
    'pandas==0.13.1',
    # 'pysal',
    # 'scipy',
    'dbfread==2.0.4',
    'networkx==1.9.1',
    'xlrd==0.9.3',
]

setup(
    name='waterkit',
    version='0.1',
    description='Water data analysis kit.',
    author='Will Dicharry',
    author_email='wdicharry@gmail.com',
    install_requires=requirements,
    packages=['waterkit'],
    test_suite="tests"
)
