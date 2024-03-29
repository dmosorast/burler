from burler.taps import Tap
from burler.streams import Stream
from burler.exceptions import TapNotDefinedException, TapRedefinedException

import re
import os
import sys
import json
import click
import singer
import singer.utils
import singer.logger as logging
from singer.catalog import Catalog
from singer.utils import load_json

LOGGER = logging.get_logger()

TAP_ROOT = None

def get_tap():
    # Accessing namespaced private member outside of class, must be prefixed with class name
    return Tap._Tap__tap

def tap(**kwargs):
    current_tap = get_tap()
    if current_tap is not None:
        raise TapRedefinedException("Attempting to redefine the global Tap object. This is not recommended to maintain a consistent state.")

    Tap._Tap__tap = Tap(**kwargs)

    return get_tap()

def check_for_tap_in_module(module):
    # Find the tap object definition for this (it should be created since we imported it
    # TODO: This is very naive, we should scoop down the submodules if possible
    objects = dir(module)

    for object_name in objects:
        tap_obj = getattr(module, object_name, None)
        if type(tap_obj) == Tap:
            return tap_obj
    return None

@click.group()
def cli():
    pass

@cli.command(name='verify',
             help="Wraps the run command with pass-through best practices verification. E.g., memory usage, output format, etc.",
             short_help="Runs the tap with best practices verification")
@click.argument('tap_name')
@click.option('--config', help='The config file for the tap.')
@click.option('--discover', '-d', is_flag=True, help='Run discovery mode.')
@click.option('--state', help='(Optional) State file to inform sync mode.')
@click.option('--catalog', help='(Optional) Catalog to specify streams and metadata for sync mode.')
def verify_tap():
    # TODO: Feature (TEST): `singer test <tap_name> <configs>` Run discovery and sync stuff, validate and look for weird things with the output! To help ensure the best practices are being upheld. Possible scoring of tap's best practices?
    # This could just check for singer best practices as we have them defined, things like memory consumption, etc.
    # It should just wrap main with this kind of validation so we can generate a report at the end of it all in the Logging
    # How does it make sense to call this?
    #    Like singer run tap-foo --verify-best-practices --discover --config /tmp/discover_config.json, etc?
    # or Like singer verify tap-foo --discover --config /tmp/tap_config.json, ?
    LOGGER.info("(NotImplemented) No tests to run yet!")

@singer.utils.handle_top_exception(LOGGER)
def execute_tap(tap_name, config, discover, state, catalog):
    try:
        module_name = re.sub('-', '_', tap_name)
        module = __import__(module_name)
    except ImportError as ex:
        if module_name in ex.msg:
            # Log and exit instead of raise since this is the result of an Exception
            LOGGER.critical("Could not import tap module '%s', please ensure that:\n- The root tap module follows underscore naming conventions\n- The tap is installed in this environment.\n\nExample (tap-foo):\n\t/\n\t/tap_foo/__init__.py\n\t/setup.py", module_name)
            sys.exit(1)
        else:
            raise

    tap_def = check_for_tap_in_module(module)
    if tap_def is None:
        raise TapNotDefinedException("Could not find an instance of Tap in module '{}'. Please ensure that it is defined at the top level module of the tap. (__init__.py or {}.py)".format(module_name, module_name))

    current_tap = get_tap()
    if tap_def is not current_tap:
        raise TapRedefinedException("Found tap definition for module {}, but it is out of sync with Burler's tap object. Please ensure that it is not being redefined.".format(module_name))

    TAP_ROOT = str.join(os.sep, module.__file__.split(os.sep)[:-1])
    #os.chdir(TAP_ROOT)

    config_json = None
    if config is not None:
        config_json = load_json(config)

    # Otherwise... lets get started!
    if discover:
        current_tap.do_discover(config_json)
    else:
        if state is not None:
            state = load_json(state)
        else:
            state = {}

        if catalog is not None:
            catalog = Catalog.load(catalog)

        current_tap.do_sync(config_json, catalog, state)

@click.command()
@click.option('--config', help='The config file for the tap.')
@click.option('--discover', '-d', is_flag=True, help='Run discovery mode.')
@click.option('--state', help='(Optional) State file to inform sync mode.')
@click.option('--catalog', help='(Optional) Catalog to specify streams and metadata for sync mode.')
def entry_point(config, discover, state, catalog):
    execute_tap(sys.argv[0].split(os.sep)[-1], config, discover, state, catalog)

@cli.command(name='run',
             help="Runs the specified singer tap with provided options, state, catalog, and configuration.",
             short_help="Runs the tap with the provided CLI options")
@click.argument('tap_name')
@click.option('--config', help='The config file for the tap.')
@click.option('--discover', '-d', is_flag=True, help='Run discovery mode.')
@click.option('--state', help='(Optional) State file to inform sync mode.')
@click.option('--catalog', help='(Optional) Catalog to specify streams and metadata for sync mode.')
def tap_main(tap_name, config, discover, state, catalog):
    execute_tap(tap_name, config, discover, state, catalog)
