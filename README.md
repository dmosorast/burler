# Burler

> **def.** [[1]](https://www.merriam-webster.com/dictionary/burler) plural -s
> 1 : one that removes loose threads, knots, and other imperfections from cloth

A library to help write taps in accordance with the [Singer specification](https://github.com/singer-io/getting-started).


# Features
- **Config file validation** `tap = Tap(config_spec=spec)` - Burler supports the following methods of validating config:
  - List Key-based inference - Takes a provided `list` of required keys and ensures that they are present
  - Dict Key-based inference - Takes a provided `dict` and validates that *ALL* its keys are present at runtime (no optional config support)
  - [Voluptuous](https://github.com/alecthomas/voluptuous) Schema - Validates according to a voluptuous Schema object
  - [schema](https://github.com/keleshev/schema) - Validates according to a schema Schema object
  - (Coming Soon) Example Config File - Same as key-based inference, but a relative file path can be specified instead of a dict object
- **Client configuration**
  - You can provide a function that creates a client object from a config object with `@tap.create_client`. This will be available on the `tap` object

# Overview
A lot of functionality provided by Burler is through decorators. This provides convenience functions or classes that configure different actions through the process of pulling data from an API. Below you will find the currently available decorators.

### Entry Point(s)

Including Burler in a project will provide a few different entry points to be used from the command line, as well as a convenience property to specify its entry point in a tap's `setup.py`.

#### singer run [tap_name]

This can be used to run one of a variety of installed taps in the current environment. 

#### singer verify [tap_name]

*(Currently Unimplemented)*

The goal of this entry point is to validate the output of a tap run, and can be used to ensure that the tap conforms to the Singer [Best Practices](https://github.com/singer-io/getting-started/blob/master/docs/BEST_PRACTICES.md#best-practices-for-building-a-singer-tap).

#### burler.entry_point

To be used in setup.py of the tap requiring the burler package, like so:

```python
import burler.entry_point
from setuptools import setup

setup(name='tap-foo',
      version='0.0.1',
...
      install_requires=[
          'burler==0.0.1',
          ...
      ],
      entry_points = {
          'console_scripts': [
              'tap-foo = ' + burler.entry_point
          ]
      },
...
)
```

### The Tap Object, Discovery Mode, and Sync Mode

Burler adopts a pattern similar to [Flask](http://flask.pocoo.org/), where the application defines a top-level object that is the source of all other configuration.

The most basic example of this is defining a function that will handle the two major modes of a tap, discovery and sync. These functions will receive parameters in the order specified in the example below.

Discovery can accept a `config` object, and Sync can accept the arguments `config, state, catalog` in that order.

```python
from burler import tap

tap = tap()

@tap.discovery_mode
def do_discover(config):
    # Do discovery...

@tap.sync_mode
def do_sync(config, state, catalog):
    # Do sync...
```

### Client Library

In order to extract data from a source, many taps use a Client library. Specifying a function that will create a client library object will add it to the tap and pass it into the places where it's needed.

***Note:*** This library currently does not need to ascribe to implement any special methods. It's just an object that is made available by the framework, and can be any object.

```python
@tap.create_client
def client(config):
    token = config["access_token"]
    return FooClient(token)
```
