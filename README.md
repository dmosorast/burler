# Burler

> **def.** [[1]](https://www.merriam-webster.com/dictionary/burler) plural -s
> 1 : one that removes loose threads, knots, and other imperfections from cloth

A library to help write taps in accordance with the [Singer specification](https://github.com/singer-io/getting-started) (and potentially targets if this pattern works out!)

# Features
- **Standard Command-Line Arguments** Burler will automatically load, validate, and parse command line arguments to call the functions that *you* care about.
- **Config file validation** `tap = burler.tap(config_spec=spec)` - Burler supports the following methods of validating config:
  - List Key-based inference - Takes a provided `list` of required keys and ensures that they are present (extra keys are passed through unchecked)
  - Dict Key-based inference - Takes a provided `dict` and validates that *ALL* of its keys are present at runtime (extra keys are passed through unchecked)
  - [Voluptuous](https://github.com/alecthomas/voluptuous) Schema - Validates according to a voluptuous Schema object
  - [schema](https://github.com/keleshev/schema) - Validates according to a schema Schema object
  - (Coming Soon) Example Config File - Same as key-based inference, but a relative file path can be specified instead of a dict object
- **Declarative Style** Most, if not all, configuration of a tap's components is performed via decorators. That way you can focus more on yielding records, and less on writing metrics!

# Overview
Burler provides multiple conveniences that can help support the development of a tap. Some of the biggest problems to solve when creating a tap are communicating with the source, defining the schema of the data, emitting records, and bookmarking at times that make sense. The goal of Burler is to remove boilerplate, so that you, the developer, can focus on the tougher stuff.

To accomplish this, a lot of the Burler framework relies on decorators. This allows you to declare functions that handle smaller pieces of the process that a tap may or must go through in order to effectively extract data. Below you will find a brief overview to get you started.

## Entry Point(s)

Including Burler in a project will provide a few different entry points to be used from the command line automatically, as well as a convenience property to specify *its* entry point in a tap's `setup.py`.

### CLI "Out of the Box"

#### singer run [tap_name]

This can be used to run one of a variety of installed taps in the current environment.

#### singer verify [tap_name]

*(Currently Unimplemented)*

The goal of this entry point is to validate the output of a tap run, and can be used to ensure that the tap conforms to the Singer [Best Practices](https://github.com/singer-io/getting-started/blob/master/docs/BEST_PRACTICES.md#best-practices-for-building-a-singer-tap).

### Convenience Property

***Setup:*** By installing burler globally, or in your virtual environment outside of the tap's installation process, you can use it as a setup helper.

#### burler.entry_point

To be used in setup.py of the tap requiring the burler package in order to provide the familiar `tap-foo --config config.json` interface, like so:

```python
import burler
from setuptools import setup

setup(name='tap-foo',
      version='0.0.1',
...
      install_requires=[
          'burler==0.0.1',
          ...
      ],
      entry_points = '''
          [console_scripts]
          tap-foo={}
      '''.format(burler.entry_point),
...
)
```

## The Tap Object, Discovery Mode, and Sync Mode

Burler adopts a pattern similar to [Flask](http://flask.pocoo.org/), where the application defines a top-level object that is the source of all other configuration.

The most basic example of this is defining a function that will handle the two major modes of a tap, discovery and sync. These functions will receive parameters in the order specified in the example below.

***Discovery:***

- Discovery can accept a `config` object.
- Discovery **must** return the catalog that was discovered (See the [Singer Getting Started Guide](https://github.com/singer-io/getting-started/blob/master/docs/DISCOVERY_MODE.md#the-catalog) for more info on the Catalog).

***Sync:***

- Sync can accept the arguments `config, catalog, state`, in that order.
- Sync is not required to return any value.

***Example:***

```python
import burler

tap = burler.tap()

@tap.discovery_mode
def do_discover(config):
    # Do discovery...

@tap.sync_mode
def do_sync(config, catalog, state):
    # Do sync...
```

## Client Library

In order to extract data from a source, many taps use a Client library (either custom, or written by a third party... fourth party in this case?). Decorating a function that creates a client library object in this manner will add it to the tap object and make it available in the places where it's needed.

***Note:***
- Burler treats the `tap.client` property as a singleton, and, as such, this function will only be called once.
- This client object currently does not need to ascribe to any patterns or implement any special methods. It's just an object that is made available by the framework, and can be any object.

***Example:***

```python
@tap.create_client
def client(config):
    token = config["access_token"]
    return FooClient(token)

def some_function():
    tap.client.make_foo_request()
```

## Defining Streams

There are two methods which you can use to define the available streams for a tap:
- Class Inheritance
- Decorator Pattern

### Class Inheritance

Burler provides a base class for streams which will transparently register the subclass as a stream with the `Tap` object. This is the most straightforward method for declaring a stream. Its "table name" that will be used to emit records will be a normalized string from the standard Python `PascalCase` for class names to `snake_case`.

```
TODO: The sub-class is expected to implement a few different methods and properties in order for the sync to succeed.
Methods: sync, get_schema, load_metadata, get_bookmark (if applicable), update_bookmark (if applicable).

load_metadata(self, schema) -> mdata (compiled metadata object, NOT .to_list())
Properties: name, replication_method, replication_key or replication_keys (must be a list), key_properties (primary keys)
```

Here is an example of using this method:

```python
TODO
```

### Decorator Pattern
TODO

### Multiple Streams Per-Class
TODO: This might actually just end up being "since decorators are just functions, you can call the decorator in a list comprehension to define multiple streams with the same class" + example
