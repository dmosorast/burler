class BurlerException(Exception):
    pass

# __init.py__
class TapNotDefinedException(BurlerException):
    pass

class TapRedefinedException(BurlerException):
    pass

# taps.py
class ConfigValidationException(BurlerException):
    pass

class SyncModeNotDefined(BurlerException):
    pass

class MissingCatalog(BurlerException):
    pass

class NoClientConfigured(BurlerException):
    pass

# schema_types.py
class NoWSDLLocationSpecified(BurlerException):
    pass

# streams.py
class DuplicateStream(BurlerException):
    pass
