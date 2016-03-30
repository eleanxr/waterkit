#! /usr/bin/env python

from setuptools import setup

requirements = [
    'setuptools',
    # Choose numpy for ArcGIS 10.2
    # 'numpy==1.7.1',
    # Choose latest numpy
    'numpy==1.9.2',
    # Choose pandas for numpy 1.7.1
    # 'pandas==0.13.1',
    # Choose latest pandas
    'pandas==0.17.1',
    'matplotlib==1.4.3',
    'pyparsing==2.0.3',
    'dbfread==2.0.4',
    'networkx==1.9.1',
    'xlrd==0.9.3',
    'openpyxl==1.8.6',
]

setup(
    name='waterkit',
    version='0.1',
    description='Water data analysis kit.',
    author='Will Dicharry',
    author_email='wdicharry@gmail.com',
    install_requires=requirements,
    packages=['waterkit'],
    test_suite="nose.collector",
    tests_require=["nose"],
)
