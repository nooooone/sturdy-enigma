#!/usr/bin/env python

from setuptools import setup

setup(
    name='indexer',
    version='0.0.1',
    description='digital ocean code challenge',
    packages=['indexer'],
    entry_points = {
          'console_scripts': [
              'indexer = indexer.__init__:main'
          ]
    },
)
