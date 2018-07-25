import os

from burler.exceptions import NoWSDLLocationSpecified

## Schema Types - its own module "from burler import tap, stream, bookmark, schema"
def json_file(filepath):
    def get_schema():
        if not os.path.isabs(filepath):
            filepath = os.path.join(os.getcwd(), path)
        with open(filepath, "r") as f:
            return json.load(f)
    return get_schema

def wsdl(url=None, filepath=None):
    def get_schema():
        # SOAP magic to get a schema from a WSDL
        if url is None and filepath is None:
            raise NoWSDLLocationSpecified("In order to specify a wsdl schema location, you must provide either a url or a filepath to locate the XSD file.")

        # TODO: Seems like there are no great python solutions to this on pypi, write our own?
        raise NotImplemented("WSDL schema definition is not currently supported. Need an XSD -> JSON Schema translator.")

        return {}
    return get_schema
