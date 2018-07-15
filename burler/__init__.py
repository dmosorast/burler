from burler.taps import Tap
from burler.streams import Stream
from burler.exceptions import TapNotDefinedException, TapRedefinedException

import re
import sys
import click
import singer
import singer.utils
import singer.logger as logging

LOGGER = logging.get_logger()

## Bookmark strategies - its own module
# TODO: Not sure the best way to implement these, they should probably configure into the do_sync method, wherever that lives...
end_of_sync = "END_OF_SYNC"

def every_n(record_count):
    def emit_bookmark():
        # check count of records emitted, if time to emit, write a bookmark with state
        pass
    return emit_bookmark

## Schema Types - its own module "from burler import tap, stream, bookmark, schema"
def json_file(filepath):
    def get_schema():
        # OS magic to determine if filepath is relative or absolute
        with open(filepath, "r") as f:
            return json.load(f)
    return get_schema

def wsdl(url=None):
    def get_schema():
        # SOAP magic to get a schema from a WSDL
        client = _tap.client
        return {}
    return get_schema

def tap(config_spec=None):
    Tap.__tap = Tap(config_spec)

    return Tap.__tap

def check_for_tap_in_module(module):
    # Find the tap object definition for this (it should be created since we imported it
    # TODO: This is very naive, we should scoop down the submodules if possible
    objects = dir(module)

    for object_name in objects:
        tap_obj = getattr(module, object_name, None)
        if type(tap_obj) == Tap:
            return tap_obj
    return None

@click.command(name='test')
def test_tap():
    LOGGER.info("(NotImplemented) No tests to run yet!")

@click.command(name='run')
@click.argument('tap_name')
@click.option('--config', help='The config file for the tap.')
@click.option('--discover', '-d', is_flag=True, help='Run discovery mode.')
@click.option('--state', help='(Optional) State file to inform sync mode.')
@click.option('--catalog', help='(Optional) Catalog to specify streams and metadata for sync mode.')
@singer.utils.handle_top_exception(LOGGER)
def main(tap_name, config, discover, state, catalog):
    """ Runs the specified singer tap with provided options, state, catalog, and configuration. """
    # TODO: Expand to run a target and differentiate them.
    # So, the vision is that this will be called with `singer run tap-foo`
    # First, check if you can load a package with the name
    # Check if it has an instance of tap
    # Verify that `config` is provided and if discovery, no catalog or state, and vice versa
    try:
        module_name = re.sub('-', '_', tap_name)
        module = __import__(module_name)
    except ImportError as ex:
        # Log and exit instead of raise since this is the result of an Exception
        LOGGER.critical("Could not import tap '%s', please ensure that the root tap module follows underscore naming conventions and is installed in this environment.\n\nExample:\n\t/\n\t\t/tap_name/__init__.py\n\t\t/setup.py", module_name)
        sys.exit(1)

    tap_def = check_for_tap_in_module(module)
    if tap_def is None:
        raise TapNotDefinedException("Could not find an instance of Tap in module '{}'. Please ensure that it is defined at the top level module of the tap. (__init__.py or {}.py)".format(module_name, module_name))

    if tap_def is not Tap.__tap:
        raise TapRedefinedException("Found tap definition for module {}, but it is out of sync with Burler's tap object. Please ensure that it is not being redefined.".format(module_name))

    # Otherwise... lets get started!
    # TODO: Parse config and validate w/ tap's definition
    if discover:
        Tap.__tap.do_discover()
    else:
        Tap.__tap.do_sync()
