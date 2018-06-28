from burler.tap import Tap
from burler.streams import Stream

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
def tap():
    # Create the tap "app" and return it
    # This might also be able to set the main entrypoint of the tap?
    # That way the user doesn't need to wrap for exceptions, or anything, but they can specify it!
    pass
