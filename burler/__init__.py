# Streams decorators
def singer_stream(cls):
    # Adds base call to different pieces that make up a stream.
    # Can a class be constructed declaratively in python?
    pass

# Class that describes the basic structure of a "tap"
class Tap:
    def __init__(self): # Keyword args? Some kind of set up config?
        self.config = None # Either a function that validates and sets config, a Schema object, or if just an array of values, do no validation and provide it via a __get__()
        self.stream_builder = lambda _: pass # Function that configures a list of streams, either through Extend, or add() that takes a stream
        # Other things required?
    
    def with_streams(self, streams):
        pass

    def run(self):
        pass
    
    def _do_discover(self):
        # Detect what has been configured and call it according to a pattern
        streams_with_discovery = [s for s in self.streams]
        pass

    def _do_sync(self):
        # Detect what has been configured and call it according to a pattern
        pass

def run_tap(args):
    # wrap exception
    # parse standard args
    # Run discovery/sync
    # Can we discover a class implementing a subclass from a function call? Meta has to support that
    pass

