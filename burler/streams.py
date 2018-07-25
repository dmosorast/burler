import re
from burler.taps import Tap

def stream(cls, name, tap_stream_id=None, stream_alias=None):
    """ A class decorator that registers a Stream class with the tap. """

    # TODO: This doesn't allow the same class to be reused for multiple streams
    cls.unique_name = lambda: tap_stream_id or name
    cls.display_name = lambda: name
    cls.emitted_name = lambda: stream_alias or tap_stream_id

    # Register cls as a stream (add to tap's map of stream classes)
    Tap.streams[cls.unique_name()] = cls

    # Set its set_context function (for the configured names)
    # Make it a subclass of Stream?
    # Provide it with implementations of sync and get_bookmark, etc that can be overriden

class StreamMeta(type):
    __pascal_case_converter = re.compile(r'(.)([A-Z][a-z]+?)')

    def __class_name_to_underscore(cls, name):
        return cls.__pascal_case_converter.sub(r'\1_\2', name).lower()

    def __init__(cls, name, bases, clsdict):
        # Check this out: https://stackoverflow.com/questions/18126552/how-to-run-code-when-a-class-is-subclassed
        if len(bases) > 0: # We only want to register classes that are sub-sub classed from this
            underscore_cls_name = cls.__class_name_to_underscore(name)
            stream(cls, underscore_cls_name)

# TODO: Should track active stream and metrics for it
class Stream(metaclass=StreamMeta):
    def __init__(self):
        # Anything to do here?
        # If this is a metaclass, it should register itself with the tap
        pass

    def sync(self, func, bookmark_strategy=None):
        self.__sync = func
        return func

    def bookmark(self, func):
        # Decorator to define bookmark accessor for stream's strategy
        pass

    def schema(self, method=None):
        # Non-decorator to declare source and method
        pass

    def schema(self, func, method=None):
        # Decorator to define methods like "generated"
        pass

    def metadata(self, func, metadata):
        # TODO: This pattern will need refined
        # TODO: Specify like { tap-foo.value: 1234, selected: true }
        # Decorator to provide the tap with what it needs to write custom metadata
        # Likely a lot of setup for this to maintain context
        pass
