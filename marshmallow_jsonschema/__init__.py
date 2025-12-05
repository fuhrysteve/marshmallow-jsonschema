from importlib import metadata

__version__ = metadata.version("marshmallow-jsonschema")
__license__ = "MIT"

from .base import JSONSchema
from .exceptions import UnsupportedValueError

__all__ = ("JSONSchema", "UnsupportedValueError")
