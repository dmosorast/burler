import json
import sys

from burler.exceptions import ConfigValidationException, SyncModeNotDefined, MissingCatalog, NoClientConfigured, StreamsNotFound

import singer
import singer.logger as logging
from singer import metrics
from singer import metadata
from singer import Transformer

from schema import Schema as SSchema, SchemaError
from voluptuous import Schema as VSchema, Invalid

LOGGER = logging.get_logger()

# Class that describes the basic structure of a "tap"
# TODO: Load streams from module? Looks in the working directory, finds the specified module and loads the streams? To eliminate the "from tap.streams import *" junk...
class Tap:
    __tap = None

    streams = {}
    debug_mode = False
    config = None
    requires_config = True
    json_encoder = None

    _discovery_override = False
    _sync_override = False
    _validate = lambda c: self.log_if_debug(LOGGER.warn, "No configuration spec provided, skipping further validation...") or c # Returns c
    # TODO: Is this necessary anymore? I think it'll just figure it out and sync no streams? Maybe warn on that.
    _sync = lambda _1, _2, _3: self._raise(SyncModeNotDefined, "No sync mode specified, please define one with the decorator @tap.sync_mode, declaring streams with subclassing burler.streams.Stream, or by declaring streams with the class decorator @burler.streams.stream")

    def _log_if_debug(self, log_func, message):
        if self.debug_mode:
            log_func(message)

    def _raise(self, exc, message):
        raise exc(message)

    def _validate_basic_conf_practices(self, conf):
        if conf is None and self.requires_config:
            raise ConfigValidationException("This tap requires a --config <file.json> argument. Please provide a configuration file.")

        if not isinstance(conf, dict):
            raise ConfigValidationException("The root of the configuration must be a JSON object.")
        # TODO: Add warnings for suggested practices? like "user_agent"?

    def validate_config(self, conf):
        _validate_basic_conf_practices(conf)
        return _validate(conf)

    def __init__(self, config_spec=None, requires_catalog=True, debug=False, json_encoder=None):
        self.requires_catalog = requires_catalog
        self.json_encoder = json_encoder

        if config_spec is None:
            self.requires_config = False

        if isinstance(config_spec, str):
            def validate(conf):
                # Load sample file, need root of schema repo.
                # Iterate over it recursivley and build up a basic schema object
                raise NotImplementedError("Specifying example schema path is not supported yet.")
            self.validate_config = validate

        if isinstance(config_spec, list):
            def validate(conf):
                self._validate_basic_conf_practices(conf)
                provided_keys = set(conf.keys())
                required_keys = set(config_spec)
                difference = required_keys - provided_keys
                if any(difference):
                    raise ConfigValidationException("Missing required configuration keys: {}".format(difference))
                return conf
            self.validate_config = validate

        if isinstance(config_spec, dict):
            def validate(conf):
                provided_keys = set(conf.keys())
                required_keys = set(config_spec.keys())
                difference = required_keys - provided_keys
                if any(difference):
                    raise ConfigValidationException("Missing required configuration keys: {}".format(difference))
                return conf
            self.validate_config = validate

        if isinstance(config_spec, VSchema):
            def validate(conf):
                try:
                    return config_spec(conf)
                except Invalid as ex:
                    raise ConfigValidationException("Error validating config: {}".format(ex)) from ex
            self.validate_config = validate

        if isinstance(config_spec, SSchema):
            def validate(conf):
                try:
                    return config_spec.validate(conf)
                except SchemaError as ex:
                    raise ConfigValidationException("Error validating config: {}".format(ex)) from ex
            self.validate_config = validate

        self.debug_mode = debug

    def _write_default_metadata(self, schema, mdata, instance = None):
        def safe_write_md(md, bc, k, v):
            return metadata.write(md, bc, k, v) if metadata.get(md, bc, k) is None else md

        if instance is None:
            instance = object()

        # Handle primary keys
        key_properties = getattr(instance, 'key_properties', None) or []
        mdata = safe_write_md(mdata, (), 'table-key-properties', key_properties)

        # Check for declared replication keys
        replication_key = getattr(instance, 'replication_key', None)
        if isinstance(replication_key, str):
            replication_keys = [replication_key]
        else:
            try:
                replication_keys = list(getattr(instance, 'replication_keys', None))
            except:
                replication_keys = []
        mdata = safe_write_md(mdata, (), 'valid-replication-keys', replication_keys)

        # Handle default replication method
        replication_method = getattr(instance, 'replication_method', None)
        if not replication_method:
            replication_method = 'INCREMENTAL' if any(replication_keys) else 'FULL_TABLE'
        mdata = safe_write_md(mdata, (), 'forced-replication-method', replication_method)

        # Write table/field selection if we can
        for field_name in schema['properties'].keys():
            if field_name in key_properties or field_name in replication_keys:
                mdata = safe_write_md(mdata, ('properties', field_name), 'inclusion', 'automatic')
            else:
                mdata = safe_write_md(mdata, ('properties', field_name), 'inclusion', 'available')
        mdata = safe_write_md(mdata, (), 'inclusion', 'available')

        return metadata.to_list(mdata)

    def __discover_using_registered_streams(self, config):
        streams = []
        for smd in self.streams.values(): # smd is StreamMetadata
            instance = smd.cls()
            smd.set_context(instance)

            if not callable(getattr(instance, 'load_schema', None)):
                instance.load_schema = lambda: {}
            if not callable(getattr(instance, 'load_metadata', None)):
                instance.load_metadata = lambda _0, _1: metadata.new()
            schema = instance.load_schema()
            streams.append({'stream': smd.display_name(),
                            'tap_stream_id': smd.unique_name(),
                            'schema': schema,
                            'metadata': self._write_default_metadata(schema,
                                                                     instance.load_metadata(schema),
                                                                     instance = instance)})

        catalog = {"streams": streams}
        return catalog

    def do_discover(self, config):
        """
        Main entrypoint for discovery mode.

        If @tap.discovery_mode is defined, it will be run first and its streams will be merged into the final catalog.
        If Stream classes have been registered, their collective catalog will be merged into the final catalog.
        All catalogs will have their metadata populated either by the registered methods, or with default values to support field selection (if possible).
        """
        self.validate_config(config)
        self.config = config

        LOGGER.info("Starting discover")

        catalog = {'streams':[]}
        if self._discovery_override:
            LOGGER.info("Found decorated discovery method, running discovery mode...")
            decorator_catalog = self._discover(config)
            # Validate metadata, write "available" and "automatic" metadata if not provided, etc
            for stream in decorator_catalog.get('streams', []):
                stream['metadata'] = self._write_default_metadata(stream['schema'], stream['metadata'])
            catalog['streams'].extend(decorator_catalog.get('streams', []))

        registered_catalog = self.__discover_using_registered_streams(config)
        catalog['streams'].extend(registered_catalog.get('streams', []))

        if not catalog['streams']:
            self.log_if_debug(LOGGER.warn, "No streams found for discovery mode. Either override discovery behavior with the decorator @tap.discovery_mode and ensure it's returning a proper catalog, or by registering Stream classes.")

        LOGGER.info("Finished discover")

        json.dump(catalog, sys.stdout, indent=2)

    def __sync_using_registered_streams(self, config, catalog, state):
        def process_record(record):
            """ Serializes data into Python objects via custom encoder. """
            if self.json_encoder:
                rec_str = json.dumps(record, cls=self.json_encoder)
                rec_dict = json.loads(rec_str)
                return rec_dict
            return record

        def stream_is_selected(mdata):
            return mdata.get((), {}).get('selected', False)

        for stream in catalog.streams:
            stream_name = stream.tap_stream_id
            mdata = metadata.to_map(stream.metadata)
            if not stream_is_selected(mdata):
                LOGGER.info("%s: Skipping - not selected", stream_name)
                continue

            singer.write_state(state)
            key_properties = metadata.get(mdata, (), 'table-key-properties')
            singer.write_schema(stream_name, stream.schema.to_dict(), key_properties)

            LOGGER.info("%s: Starting sync", stream_name)
            # Refactor Note: Start of stream sync
            smd = self.streams.get(stream.tap_stream_id)
            if smd is None:
                continue # We want to allow both a sync decorator and registered streams
            instance = smd.cls()
            smd.set_context(instance)

            # If we have a bookmark, use it; otherwise use start_date
            ## META: Write stream into state object's bookmarks map
            if (instance.replication_method == 'INCREMENTAL' and
                    not state.get('bookmarks', {}).get(stream.tap_stream_id)):
                singer.write_bookmark(state,
                                      stream.tap_stream_id,
                                      instance.replication_key,
                                      config.get('start_date'))

            ## META: Check if "sync" is defined
            with metrics.record_counter(stream.tap_stream_id) as counter:
                # TODO: This will need to unwrap (StreamClass, record) for sub-streams
                for record in instance.sync(state):
                    counter.increment()

                    rec = process_record(record)
                    with Transformer() as transformer:
                        rec = transformer.transform(rec, stream.schema.to_dict(), metadata.to_map(stream.metadata))

                    singer.write_record(stream.tap_stream_id, rec)

                ## META: Bookmark stratey comes in here
                if instance.replication_method == "INCREMENTAL":
                    singer.write_state(state)

                LOGGER.info("%s: Completed sync (%s rows)", stream_name, counter.value)
            # Refactor Note: End of stream sync

        singer.write_state(state)
        LOGGER.info("Finished sync")

    def do_sync(self, config, catalog, state):
        """
        Main entrypoint for sync mode.

        If a sync mode function is declared with the decorator, it will receive a catalog with all streams that do not have classes defined.
        If a stream class is registered for a tap_stream_id, it will be executed according to the class's members.
        If both are defined, the Stream class takes precedence. This is to help partial migration.
        """
        self.validate_config(config)
        self.config = config

        if self.requires_catalog and catalog is None:
            raise MissingCatalog("Please provide a catalog file. This tap requires a catalog to be specified using --catalog <file.json>.")

        if self._sync_override:
            LOGGER.info("Found decorated sync method, running sync mode...")
            # TODO: Is it confusing to modify the catalog? If a stream class is registered, it should take precedence, I think
            non_registered_catalog = {'streams': [s for s in catalog['streams'] if stream.tap_stream_id in self.streams]}
            self._sync(config, non_registered_catalog, state)

        self.__sync_using_registered_streams(config, catalog, state)

    def load_streams(self, module_name):
        """
        Loads the module specified to register the streams it contains.
        """
        try:
            __import__(module_name)
        except ImportError as ex:
            raise StreamsNotFound("Could not import module '{}' to load streams. Ensure that the Python module path is correct. e.g., tap_foo.streams.invoices".format(module_name)) from ex

    # Tap decorators
    def discovery_mode(self, func):
        self._discover = func
        self._discovery_override = True
        return func

    def sync_mode(self, func):
        self._sync = func
        self._sync_override = True
        return func

    # NB: It seems that properties are configured at class creation, so to have
    #     a decorator that configures a property getter, we need a passthrough
    #     function that gets assigned at decorator evaluation time (post Tap
    #     object creation.
    __client = None
    __configured_client_constructor = None
    def __get_client(self):
        if self.__configured_client_constructor:
            return self.__configured_client_constructor()
        raise NoClientConfigured("No client configured, configure a client object using @tap.create_client")

    client = property(__get_client)
    def create_client(self, func):
        # Decorator that grabs the client, given a config
        def get_client():
            if self.__client is None:
                self.__client = func(self.config)
            return self.__client
        self.__configured_client_constructor = get_client
        return func
