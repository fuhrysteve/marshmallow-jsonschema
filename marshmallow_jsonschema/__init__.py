from importlib.metadata import version

__version__ = version("marshmallow-jsonschema")
__license__ = "MIT"

from .base import JSONSchema
from .exceptions import UnsupportedValueError

__all__ = ("JSONSchema", "UnsupportedValueError")
