"""
Contains functions and classes for streamlining the registration and execution of
streams by hooking them up to the global `tap` object.
"""
import re
from burler.taps import Tap
from burler.exceptions import DuplicateStream

def _raise_duplicate_stream(name):
    raise DuplicateStream(("Attempted to register duplicate stream ({}) using Stream "
                           "class. For a single class that handles multiple stream "
                           "names, use the decorator with a unique name:\n\n"
                           "\t@stream(\"my_stream\", tap_stream_id=\"invoices\")\n"
                           "\t@stream(\"my_stream\", tap_stream_id=\"contacts\")\n"
                           "\tclass MyStream():\n\t\t...").format(name))

_pascal_case_converter = re.compile(r'(.)([A-Z][a-z]+?)')

def _class_name_to_underscore(name):
    return _pascal_case_converter.sub(r'\1_\2', name).lower()

def stream(name=None, tap_stream_id=None, stream_alias=None): # pylint: disable=unused-argument
    """ A class decorator that registers a Stream class with the tap. """

    def wrapped_stream(cls):
        nonlocal name
        if not name:
            name = _class_name_to_underscore(cls.__name__)

        class StreamMetadata():
            """
            Metadata class that allows the Tap to use values configured during the
            tap run, and allows decorators to modify the definition of a
            stream's methods on the fly.
            """
            def __init__(self, cls, name, tap_stream_id, stream_alias):
                self.cls = cls
                self.unique_name = lambda: tap_stream_id or name
                self.display_name = lambda: name
                self.emitted_name = lambda: stream_alias or tap_stream_id

            def set_context(self, instance): # pylint: disable=no-self-use
                """
                Sets the context to be used when calling the sync methods. This gives
                it bookmarks, catalog, etc.
                """
                current_tap = Tap._Tap__tap # pylint: disable=protected-access
                instance.client = current_tap.client

        smd = StreamMetadata(cls, name, tap_stream_id, stream_alias)
        if smd.unique_name() in Tap.streams:
            _raise_duplicate_stream(smd.unique_name())

        # Register cls as a stream (add to tap's map of stream classes)
        Tap.streams[smd.unique_name()] = smd

        # Make it a subclass of Stream?
        # Provide it with implementations of sync and get_bookmark, etc that can be overriden

        return cls
    return wrapped_stream

class StreamMeta(type):
    """
    Meta-class that allows us to automatically register streams with the
    global `tap` when the `Stream` class is subclassed (at load time).
    """
    def __init__(cls, name, bases, clsdict):
        super().__init__(cls, name, bases, clsdict)
        # More Info:
        # https://stackoverflow.com/questions/18126552/how-to-run-code-when-a-class-is-subclassed
        if len(bases) > 0: # We only want to register classes that are sub-sub classed from this
            underscore_cls_name = _class_name_to_underscore(name)
            if underscore_cls_name in Tap.streams:
                _raise_duplicate_stream(underscore_cls_name)
            stream(underscore_cls_name)(cls) # Call decorator wrapper explicitly

# TODO: Should track active stream and metrics for it
class Stream(metaclass=StreamMeta):
    """
    The main Stream parent class to provide Singer-related instrumentation
    around the actions of a Stream subclass.
    """
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
