from pkg_resources import get_distribution

__version__ = get_distribution('marshmallow-jsonschema').version
__license__ = 'MIT'

from .base import dump_schema

__all__ = (
    'dump_schema'
)
