#!/usr/bin/env python

from setuptools import setup

import pkg_resources

def load_tap_name():
    """ Tries to determine the name of the tap for generating the entry point. """
    ws = pkg_resources.WorkingSet()
    # TODO: This could be smarter, like look at the module that has a "tap" object
    matches = [s.key for s in ws if s.key.startswith("tap")]
    print([s.key for s in ws])
    if not matches:
        #raise Exception(str(sys.prefix) + "\n" + str(sys.base_prefix))
        # TODO: This is flawed. There's a circular dependency issue here.
        # We can't really check the thing that depends on this from this, unless there's some bootstrapping way we can check the modules from install only
        # Is ther an "on required" kind of thing?
        return "singer"
        raise Exception("No module named 'tap...' found. Burler must be installed in a tap project's directory.")
    return matches[0]

setup(name='burler',
      version='0.0.1',
      description='Extensions to the python standard library for Singer.',
      author='Stitch',
      url='https://singer.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      install_requires=[
          'singer-python==5.1.5',
      ],
      py_modules=['burler'],
      entry_points={
        'console_scripts': [
            load_tap_name() + ' = burler:main', # TODO: The entry point should be dynamic somehow...
        ],
    },
)
