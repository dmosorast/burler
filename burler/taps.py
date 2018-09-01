import json
import sys

from burler.exceptions import ConfigValidationException, SyncModeNotDefined, MissingCatalog, NoClientConfigured

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
    _validate = lambda c: self.log_debug(LOGGER.warn, "No configuration spec provided, skipping further validation...") or c # Returns c
    # TODO: Check if discovery is required with a class function
    _discover = lambda _: self.log_debug(LOGGER.warn, "No discovery mode specified. If needed, define one with the decorator @tap.discovery_mode, skipping discovery")
    _sync = lambda _1, _2, _3: self._raise(SyncModeNotDefined, "No sync mode specified, please define one with the decorator @tap.sync_mode")

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

    def __discover_using_registered_streams(self, config):
        LOGGER.info("Starting discover")

        streams = []
        for smd in self.streams.values(): # s is StreamMetadata
            instance = smd.cls()
            smd.set_context(instance)
            # TODO: Check to see that load_schema and load_metadata are specified on these classes
            streams.append({'stream': smd.display_name(), 'tap_stream_id': smd.unique_name(), 'schema': instance.load_schema(), 'metadata': instance.load_metadata()})

        catalog = {"streams": streams}
        json.dump(catalog, sys.stdout, indent=2)
        LOGGER.info("Finished discover")

    def do_discover(self, config):
        """ Main entrypoint for discovery mode. """
        self.validate_config(config)
        self.config = config

        if self._discovery_override:
            LOGGER.info("Found decorated discovery method, running discovery mode...")
            self._discover(config)
            return

        # TODO: How to check if discovery mode is not available? If no load_schema or load_metadata appear on any of the classes?
        self.__discover_using_registered_streams(config)

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
            smd = self.streams[stream.tap_stream_id]
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
        """ Main entrypoint for sync mode. """
        self.validate_config(config)
        self.config = config

        if self.requires_catalog and catalog is None:
            raise MissingCatalog("Please provide a catalog file. This tap requires a catalog to be specified using --catalog <file.json>.")

        if self._sync_override:
            LOGGER.info("Found decorated sync method, running sync mode...")
            self._sync(config, state, catalog)
            return

        self.__sync_using_registered_streams(config, catalog, state)

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
