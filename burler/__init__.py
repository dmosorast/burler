# Streams decorators
def singer_stream(cls):
    # Adds base call to different pieces that make up a stream.
    # Can a class be constructed declaratively in python?
    pass

# Class that describes the basic structure of a "tap"
class Tap:
    def __init__(self): # Keyword args? Some kind of set up config?
        self.config = None # Either a function that validates and sets config, a Schema object, or if just an array of values, do no validation and provide it via a __get__()
        self.stream_builder = lambda _: pass # Function that configures a list of streams, either through Extend, or add() that takes a stream
        # Other things required?
    
    def with_streams(self, streams):
        pass

    def run(self):
        pass
    
    def _do_discover(self):
        # Detect what has been configured and call it according to a pattern
        streams_with_discovery = [s for s in self.streams]
        pass

    def _do_sync(self):
        # Detect what has been configured and call it according to a pattern
        pass

def run_tap(args):
    # wrap exception
    # parse standard args
    # Run discovery/sync
    # Can we discover a class implementing a subclass from a function call? Meta has to support that
    pass

# Helper to make it easier to write/read/declare? metadata

# Declarative schema making? Like node().type("string").nullable()


#### How do I want this to be called?
Tap().with_streams(Streams).run() # Simple stream list method

Tap(lambda streams: # 
    # configure the tap run process here?
    streams.extend([Stream1, Stream2])
    streams.add(Stream()
                .with_sync_mode(sync_stream)
                .with_discover_mode(get_schema)
                .with_bookmarks(get_bookmark, save_bookmark))
)
.with_client() # Configure client to pass through to streams
.with_config() # Schema implementation? Maybe this could wrap schema with convenience functions for declaring common schemas
.run(args)

####### Alternative Stream configuration, limits the need for classes, reduces the imports required
stream
.schema(discovery_func)
.bookmarking(get_bookmark, set_bookmark)
.sync(get_data)

# One of the good things about fluent style is that multiple standard options can be provided from each step.
# - Like stream -> either schema or sync, bookmarking can go through in there. It only sucks if the class returned is exactly the same and doesn't describe a configuration flow.

### What does a stream need?
# - A function that takes a client, state, catalog, etc. and yields data
# - A method of looking up and setting bookmarks
# - A way to describe its schema
# - A way to write metadata to that schema
#      - Can these be intertwined? (metadata is called with each node in the schema, so it's basically a "visit()")

#### Flask Style Decorators
tap = burler.tap(client, config_spec=None) # config could either be an example, Schema, or function that validates config and throws when failed. If None, no config required

## Passes in configuration pulled from command line, after validation
@tap.client
def configure_client(config):
    return CoolTapClient(config["base_url"], config["access_token"])

## Bookmark Strategy: end_of_stream, every_100, every_n(352)
# Only called if marked selected
@tap.sync("contacts", bookmark_strategy="end_of_sync")
def get_contacts(client):
    current_bookmark = tap.get_bookmark() # Context aware setting of this function via decorator
    my_cool_metadata = tap.stream_metadata() # {tap-thing.value1: 1234, selected: true}
    yield client.get_contacts(current_bookmark)

## Given a record and the existing state, return the bookmark value
# Bookmarks will get saved via stream name and strategy specified with sync
@tap.bookmark("contacts")
def get_bookmark(record):
    return record["date_modified"]

## Get the schema for a stream
# Methods: File, Generated (Default), WSDL (auto-parsing? passes it in to be modified?)
# Can you decorate a value? or just call it maybe?
tap.schema("contacts", method=burler.json_file("schemas/contacts.json"))

# WSDL schema could be specified like this, with optional parsing function? I wonder if suds or something could help with this
tap.schema("contacts", method=wsdl(url="http://www.things.com/v43/wsdl.xml"))

# Generated
@tap.schema("contacts", method=generated)
def get_schema():
    schemas = tap.client.describe()
    return {n["name"], to_json_schema(n["value"]) for n in schemas["objects"]}

## Write Metadata to Schema
# Breadcrumb should have: name, path, level
@tap.metadata("contacts")
def write_metadata(breadcrumb, sub_schema):
    if breadcrumb.level == 0:
        tap.write_metadata("key_properties", ["contact_id"])
    if breadcrumb.level == 1:
        tap.write_metadata("inclusion", "available")
    if breadcrumb.name in tap.key_properties: # In practice, inclusion automatic should be handled already
        tap.write_metadata("inclusion", "automatic")

## Outstanding Questions
#### Perhaps putting variable functions on "tap" doesn't make much sense
####     - Is it awkward to have a magical "stream" object that the decorator updates?
####     - like `from burler import stream` then that is a reference to an object that gets modified by the decorators for use in context
#### How to do stream dependencies?
#### Config options that support WSDLs?
