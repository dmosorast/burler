# Class that describes the basic structure of a "tap"
# TODO: Debug level logging? Like log when an assumption is made? Like "No config spec found, continuing without config validation. See github.com/dmosorast/burler/README.md#config-validation"
# TODO: Custom exceptions for when a sync isn't defined, etc.
class Tap:
    def __init__(self, config_spec=None, debug=False):
        # - Interpret args
        # - Validate schema if: Schema, matches basic data types in config example, or call function
        #   configured with config as parameter, if None, then validation is a no-op
        # - Set up debug level logging if configured
        pass

    def client(self, func):
        # Decorator that grabs the client, given a config
        self.client = func(self.config)

# TODO: Should track active stream and metrics for it
class Stream:
    # TODO: This could be a static class
    # It might be nice to just use @stream.contacts.sync() and implement __attr__ to create if not exists
    # TODO: Not sure how to implement attr on a static class
    def __init__(self):
        # Anything to do here?
        raise Exception()
        pass

    def sync(self, func, bookmark_strategy=None):
        # Decorator to define sync for stream name
        pass

    def bookmark(self, func):
        # Decorator to define bookmark accessor for stream's strategy
        pass

    def schema(self, method=None):
        # Non-decorator to declare source and method
        pass

    def schema(self, func, method=None):
        # Decorator to define methods like "generated"
        pass

    def metadata(self, func):
        # TODO: This pattern will need refined
        # Decorator to provide the tap with what it needs to write custom metadata
        # Likely a lot of setup for this to maintain context
        pass

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
