from burler.exceptions import ConfigValidationException

import singer.logger as logging

from schema import Schema as SSchema, SchemaError
from voluptuous import Schema as VSchema, Invalid

LOGGER = logging.get_logger()

# Class that describes the basic structure of a "tap"
# TODO: Debug level logging? Like log when an assumption is made? Like "No config spec found, continuing without config validation. See github.com/dmosorast/burler/README.md#config-validation"
# TODO: Custom exceptions for when a sync isn't defined, etc.
class Tap:
    __tap = None

    debug_mode = False
    _validate = lambda c: LOGGER.warn("No configuration spec provided, skipping further validation...") or c # Returns c

    def _validate_basic_conf_practices(self, conf):
        if not isinstance(conf, dict):
            raise ConfigValidationException("The root of the configuration must be a JSON object.")
        # TODO: Add warnings for suggested practices? like "user_agent"?

    def validate_config(self, conf):
        _validate_basic_conf_practices(conf)
        return _validate(conf)

    def __init__(self, config_spec=None, debug=False):
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


    # "MAIN DISCOVER/SYNC FUNCTIONS"
    # Step 1: Validate config against the provided spec, if any.
    # - If no config, print (debug-level) "No config required for this tap, skipping validation."
    # - Is no config provided, exit w/ "No config provided, please provide a config of the format: <Schema or sample config text>"
    # If config provided, validate against configured Schema and continue
    def do_discover(self, config):
        if self.config_schema is not None:
            self.config_schema.validate(config)
        # Do the magic with finding streams and their implementations, or just grabbing a pass-through do_discover configured by the caller
        pass

    def do_sync(self, config):
        if self.config_schema is not None:
            self.config_schema.validate(config)
        # Do the magic with finding streams and their implementations, or just grabbing a pass-through do_sync configured by the caller
        pass


    def client(self, func):
        # Decorator that grabs the client, given a config
        self.client = func(self.config)
