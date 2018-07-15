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
          'click==6.7',
          'schema==0.6.8',
          'voluptuous==0.11.1'
      ],
      py_modules=['burler'],
      entry_points={
        'console_scripts': [
            'singer = burler:cli',
        ],
    },
)

# GOAL: To enable speed of review by limiting noise and being opinionated about tap structure


# Feature: stream-error ("Erroy syncing stream %s - {message}") wraps exceptions thrown from sync code
# Feature: "Sub Stream" - See TicketAudits in tap-zendesk, needs to emit schemas in a transitive dependency-friendly way
# Feature: Buffer yielding for sub streams - Wrap the generator in a loop that will read until a certain amount of time has passed and then yield back to the sync loop
# Feature: Sub stream split bookmark tracking, for dependent streams, bookmarks should roll up to each parent level above the last
