#!/usr/bin/env python

from setuptools import setup

setup(name='burler',
      version='0.0.1',
      description='Extensions to the python standard library for Singer.',
      author='Stitch',
      url='https://singer.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      install_requires=[
          'singer-python==5.1.5',
      ]
)
