from burler.taps import Tap
from burler.streams import Stream

import pkg_resources

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

# TODO: Not sure of the best pattern for this, so that streams can access tap for their decorators
# - Maybe a static accessor on the Tap class? With one set before tap() returns it
_tap = None
def tap(config_spec=None):
    # Create the tap "app" and return it
    # This might also be able to set the main entrypoint of the tap?
    # That way the user doesn't need to wrap for exceptions, or anything, but they can specify it!
    _tap = Tap(config_spec)

    return _tap

def main():
    """ This is the entry point for a tap run, just like in a tap, this will parse args, and run discovery/sync. """

    import re
    import sys
    import os

    ws = pkg_resources.WorkingSet()
    module_paths = set()
    for s in ws:
        # Check if we have a burler dependency to limit search space
        burler_dep = [d for d in s.requires() if d.name == "burler"]
        if burler_dep:
            # TODO: TEST THIS WITH DIFFERENT DEPLOY METHODS, MIGHT NOT WORK
            module_paths.add(s.from_filename("").location)

    modules_to_load = []
    for path in module_paths:
        for subdir, dirs, files in os.walk(path):
            for f in files:
                if subdir[len(path) + 1:].count(os.sep) >= 2:
                    continue
                if f == "__init__.py":
                    modules_to_load.append(subdir.split(os.sep)[-1])
#                if f.endswith(".py"):
                    # TODO: This needs to be aware of the base path and use a dot notation to import I think
#                    modules_to_load.append(f[0:-3])

    for m in modules_to_load:
        if m == "burler":
            continue
        try:
            if m == "tap_zendesk_burler":
                import pdpb
                pdb.set_trace()
            module = __import__(m)
            print("Import success! {}".format(m))
            import pdb
            pdb.set_trace()
            if getattr(module, "tap", None):
                print(m)
        except ImportError as ex:
            # TODO: This should probably re-raise if thrown from inside the module (see Flask)
            #print("IMPORT ERROR on module {}, exception".format(m, ex))
            pass

    # for module in sys.modules:
    #     if getattr(sys.modules[module], "tap", None) and module != "burler":
    #         print(dir(module))
    # TODO: There's a chance this can be run from the command "singer" I think  that's handled if we don't find a tap class? This could ship off to singer-tool thoush in that case... hmmm...
    print("Hello CLI!")

# Not sure if this is doable or useful
def setup(name=None,
          version=None,
          description=None,
          author=None,
          url=None,
          install_requires=[]):
    """ Take the relevant tap parameters and run setup using setuptools. """
    setuptools.setup(name='tap-zendesk-burler',
                     version='0.0.1',
                     description='Singer.io tap for extracting data from the Zendesk API',
                     author='Stitch',
                     url='https://singer.io',
                     classifiers=['Programming Language :: Python :: 3 :: Only'],
                     py_modules=[name.replace('-','_')],
                     install_requires=[
                         'singer-python==5.1.5',
                         'zenpy==2.0.0',
                         'burler==0.0.1'
                     ],
                     packages=[name.replace('-', '_')],
                     include_package_data=True,
)
