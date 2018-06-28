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
