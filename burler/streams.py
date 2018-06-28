# TODO: Should track active stream and metrics for it
class Stream:
    # TODO: This could be a static class
    # It might be nice to just use @stream.contacts.sync() and implement __attr__ to create if not exists
    # TODO: Not sure how to implement attr on a static class
    def __init__(self):
        # Anything to do here?
        raise Exception()
        pass

    def sync(self, func, bookmark_strategy=None):
        # Decorator to define sync for stream name
        pass

    def bookmark(self, func):
        # Decorator to define bookmark accessor for stream's strategy
        pass

    def schema(self, method=None):
        # Non-decorator to declare source and method
        pass

    def schema(self, func, method=None):
        # Decorator to define methods like "generated"
        pass

    def metadata(self, func):
        # TODO: This pattern will need refined
        # Decorator to provide the tap with what it needs to write custom metadata
        # Likely a lot of setup for this to maintain context
        pass
