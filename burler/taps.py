
from burler.exceptions import ConfigValidationException, SyncModeNotDefined, MissingCatalog, NoClientConfigured

import singer.logger as logging

from schema import Schema as SSchema, SchemaError
from voluptuous import Schema as VSchema, Invalid

LOGGER = logging.get_logger()

# Class that describes the basic structure of a "tap"
class Tap:
    __tap = None

    debug_mode = False
    config = None
    requires_config = True
    _validate = lambda c: self.log_debug(LOGGER.warn, "No configuration spec provided, skipping further validation...") or c # Returns c
    _discover = lambda _: self.log_debug(LOGGER.warn, "No discovery mode specified, if needed define one with the decorator @tap.discovery_mode, skipping discovery")
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

    def __init__(self, config_spec=None, requires_catalog=True, debug=False):
        self.requires_catalog = requires_catalog

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

    def do_discover(self, config):
        """ Main entrypoint for discovery mode. """
        self.validate_config(config)
        self.config = config
        # TODO: Use configured streams and embark on standard discovery process
        self._discover(config)

    def do_sync(self, config, state, catalog):
        """ Main entrypoint for sync mode. """
        self.validate_config(config)
        self.config = config
        if self.requires_catalog and catalog is None:
            raise MissingCatalog("This tap requires a catalog to be specified using --catalog <file.json>. Please provide a catalog file.")
        # TODO: Use configured streams and embark on standard sync process
        self._sync(config, state, catalog)

    # Tap decorators
    def discovery_mode(self, func):
        self._discover = func
        return func

    def sync_mode(self, func):
        self._sync = func
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
