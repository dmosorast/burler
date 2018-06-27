# Class that describes the basic structure of a "tap"
class Tap:
    def __init__(config_spec=None):
        # Interpret args
        # Validate schema if: Schema, matches basic data types in config example, or call function
        # configured with config as parameter, if None, then validation is a no-op
        pass

def run_tap(args):
    # wrap exception
    # parse standard args
    # Run discovery/sync
    # Can we discover a class implementing a subclass from a function call? Meta has to support that
    pass

def tap():
    # Create the tap "app" and return it
    # This might also be able to set the main entrypoint of the tap?
    # That way the user doesn't need to wrap for exceptions, or anything, but they can specify it!
    pass
