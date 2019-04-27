# Overall
GOAL: To enable speed of review by limiting noise and being opinionated about tap structure

# Test Tap Ideas
- Monday.com - https://developers.monday.com/
  - Been seeing their ads on youtube, so might be nice to have

# Outstanding Base Features
- (Architecture) Refactor out CLI
- (Discovery Feature) Add support to resolve all varieties of schema references
X Add Stream base class
  - (Sync Feature) Constants for replication method (Full Table, Key-Based Incremental, etc.)
  X (Architecture) Load streams from module? To be used in place of "from tap.streams import *" in the root file
  - (Sync Feature) Provide handling for "INCREMENTAL" and "FULL_TABLE" (e.g., version tracking, activate version messages, etc.)
    - `with full_table():` block to help with using the `ActivateVersionMessage`
  - (Sync Feature) `emit_record` and `emit_records` that takes a list of records and emits them from the current stream class.
    - This is so that we can emit records directly to the tap's output and wrap it in the stream type, to handle weird substream situations
    - I imagine this would be preloaded with a function that calls a function on tap that will do a sub-portion of sync
    - Should wrap the emitted records in a tuple to identify the stream they belong to
    - Provide `stream="blah"` override to support classes handling two streams (like with a GraphQL endpoint)
- (Sync Feature) Add the ability to specify a post-transform-hook (a la adwords)
- (Logging) Add standard informational logging for starting tap, starting stream, etc.
- (Metrics) Add standard metrics
- (Config Spec) Implement loading a sample config file from a relative path for dict-based validation (or absolute path. Why not?)
- (Config Spec) Allow passing in a validation function that will throw if invalid
- Error Handling: Run all streams if possible, catch errors and fail with "CRITICAL stream: error" at the end
  - stream-error ("Erroy syncing stream %s - {message}") wraps exceptions thrown from sync code
- (Architecture) "Sub Stream" - See TicketAudits in tap-zendesk or tap-harvest V2 functional substreams, needs to emit schemas in a transitive dependency-friendly way
  - Buffer yielding for sub streams - Wrap the generator in a loop that will read until a certain amount of time has passed and then yield back to the sync loop
  - Sub stream split bookmark tracking, for dependent streams, bookmarks should roll up to each parent level above the last
    - This is a harder problem than originally thought, due to lack of ordering guarantees
    - To catch all of the data, we would need:
      1. A bookmark key on the child
      2. Propagation of that bookmark to the parent objects
      3. A lookback window on the child bookmark to ensure that no async changes are missed that were made mid-sync.
    - This is better handled by the implementer, to take advantage of semantic knowledge of the source
- (Sync Feature) Sync Context
  - Needs to write and read "currently-syncing" state value (for sub-streams, should handle parent/sub level)
  - Should provide `start_date`
- (Architecture) Functional style, e.g., `@stream("thing")`, `@stream("thing").sync("sync_a_thing")`, `@stream("thing").substream("child_thing").sync("get_child_for_thing")`, etc.
- (Verify Mode) Check catalog from discovery for unpublishable metadata
- (Verify Mode) Check that the tap doesn't blow up when both properties and a catalog are passed in
- (Sync Mode, Testing) Set of "monkeypatches" that add assertions to common tap calls, like write_record, request.get, write_bookmark, etc.
  - Bookmark MUST advance by some multiple of time (threshold for WARN? based on ratio of advancement to run time?)
  - Removed Paths (different paths, etc) Generate a schema that would match during the run.
  - burler.spec module?
  - Assert that the Ordering of records being returned from an API are as expected (e.g., @ensure_ordering('created_at', 'ASC') around the call that returns records)
  - Instrumentation to track bookmark advancement rate
- (Patterns) Add patterns for sync styles, e.g., windowing, full-request-incremental-emit, etc.
- (Architecture) Instead of pigeonholing into a framework, split into modules like `burler.config`, `burler.spec`, etc. that contain the pieces used by the automated Singer structure method.
  - That way people can grab the niceties without committing to the framework

# Potential Enhancements
- Report of rows synced/updated a-la tap-stripe at the end of the run
- Different types of abstractions (database use cases, bulk api, csv export?, variable stream types [specify multiple streams per class])
  - "For thing" sync mode. e.g., "function that returns list of accounts" -> "for each account, call sync"
- Retry sync? Function to restart the sync for a stream from the original bookmark, or with a current bookmark override.
  - E.g., when tap-zuora fails on a 404 for a sub-file to retry the original sync instead of bombing out
  - Could be on stream spec like `@stream("thing", retry_sync_on=NotFoundException, setup_retry=reset_file_bookmarks)`
- Client library stub generation? - The client library concept will need more guidance. I can envision something like Client.generate([list, of, endpoints]) as a decorator and it will mark up the class with functions to make calls to the specified endpoints as POST, PUT, GET, etc. For each verb needed.
  - Retry with backoff on sync requests? or the ability to specify it? (might be best to just leave it up to the user)
    - a la "backoff_strategy" on the client with a stub request that calls user-specified "request"
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
#      - The goal here being to remove the boilerplate "write primary keys, write replication key, loop over top-level properties"
#          - Already handled with Tap's "write default metadata" for the most part.

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

-- OR --

# Have convenience methods for standard keys, e.g., inclusion, selected, etc.
class Inclusion():
    def automatic(self):
        pass
    def unsupported(self):
        pass
    def available(self):
        pass # default if not called

class FieldMetadata():
    inclusion =
schema_field.inclusion.automatic # Property that writes the metadata in context


## Outstanding Questions
#### Perhaps putting variable functions on "tap" doesn't make much sense
####     - Is it awkward to have a magical "stream" object that the decorator updates?
####     - like `from burler import stream` then that is a reference to an object that gets modified by the decorators for use in the enclosing function context
#### How to do stream dependencies?
#### Config options that support WSDLs?
#### Convenience abstractions for GraphQL APIs? What does this look like?
#### Credentials refresh options on the client? Like periodic(refresh_func, min=25), or one_time(refresh_func)
```
