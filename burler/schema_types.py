import os

from burler.exceptions import NoWSDLLocationSpecified

## Schema Types
## These functions will be called and return a function to get the schema for a specific stream
def json_file(filepath):
    """ Loads a JSON Schema from a filepath. """
    def get_schema():
        if not os.path.isabs(filepath):
            filepath = os.path.join(os.getcwd(), path)
        with open(filepath, "r") as f:
            return json.load(f)
    return get_schema

def wsdl(url=None, filepath=None):
    """ Loads a WSDL file and converts it to JSON schema as best it can. """
    def get_schema():
        # SOAP magic to get a schema from a WSDL
        if url is None and filepath is None:
            raise NoWSDLLocationSpecified("In order to specify a wsdl schema location, you must provide either a url or a filepath to locate the XSD file.")

        # TODO: Seems like there are no great python solutions to this on pypi, write our own?
        raise NotImplemented("WSDL schema definition is not currently supported. Need an XSD -> JSON Schema translator.")

        return {}
    return get_schema

def discovered(discovery_func):
    """ Uses a function that loads the schema from some non-standard source (such as a describe API endpoint. """
    # We can wrap this function with validation if necessary
    # TODO: What parameters to pass into the function? This needs defined in the Stream class.
    return discovery_func
