class BurlerException(Exception):
    pass

class TapNotDefinedException(BurlerException):
    pass

class TapRedefinedException(BurlerException):
    pass

class ConfigValidationException(BurlerException):
    pass

class SyncModeNotDefined(BurlerException):
    pass

class MissingCatalog(BurlerException):
    pass

class NoClientConfigured(BurlerException):
    pass
