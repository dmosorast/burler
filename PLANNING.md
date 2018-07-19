# Overall
GOAL: To enable speed of review by limiting noise and being opinionated about tap structure

# Outstanding Base Features
- Answer the question: Should discovery return the catalog? or should it write out.
  - Returning the catalog would help add validation around it from the framework perspective. Then Burler can write it out
- Add Stream base class
- Add Magic sync and discovery modes that use configured Stream base classes (if they exist)
- Add standard informational logging for starting tap, starting stream, etc.
- Add standard metrics
- Implement loading a sample config file from a relative path for dict-based validation (or absolute path. Why not?)

# Potential Enhancements
- stream-error ("Erroy syncing stream %s - {message}") wraps exceptions thrown from sync code
- "Sub Stream" - See TicketAudits in tap-zendesk, needs to emit schemas in a transitive dependency-friendly way
  - Buffer yielding for sub streams - Wrap the generator in a loop that will read until a certain amount of time has passed and then yield back to the sync loop
  - Sub stream split bookmark tracking, for dependent streams, bookmarks should roll up to each parent level above the last
- Client library stub generation? - The client library concept will need more guidance. I can envision something like Client.generate([list, of, endpoints]) as a decorator and it will mark up the class with functions to make calls to the specified endpoints as POST, PUT, GET, etc. For each verb needed.
- (Perhaps with targets) Writing state messages to a file? -o --out-file option to support writing State messages to a file before emitting them? (may actually require monkey patching singer.write_message)

# Brainstorming

Some thoughts on how this library will look, overall. Flask-style app declaration with its own decorators to declare streams' methods.

```
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
####     - like `from burler import stream` then that is a reference to an object that gets modified by the decorators for use in the enclosing function context
#### How to do stream dependencies?
#### Config options that support WSDLs?
#### Credentials refresh options on the client? Like periodic(refresh_func, min=25), or one_time(refresh_func)
```
