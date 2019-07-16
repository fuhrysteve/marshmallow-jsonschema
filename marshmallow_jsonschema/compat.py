import sys
import marshmallow

PY2 = int(sys.version_info[0]) == 2
MARSHMALLOW_MAJOR_VERSION = int(marshmallow.__version__.split(".", 1)[0])

if PY2:
    text_type = unicode
    binary_type = str
    basestring = basestring
else:
    text_type = str
    binary_type = bytes
    basestring = (str, bytes)


if MARSHMALLOW_MAJOR_VERSION == 2:

    def dot_data_backwards_compatible(json_schema):
        return json_schema.data

    def list_inner(list_field):
        return list_field.container


else:

    def dot_data_backwards_compatible(json_schema):
        return json_schema

    def list_inner(list_field):
        if hasattr(list_field, "container"):
            # backwards compatibility for marshmallow versions prior to 3.0.0rc8
            return list_field.container

        return list_field.inner


__all__ = (
    "text_type",
    "binary_type",
    "basestring",
    "list_inner",
    "dot_data_backwards_compatible",
    "MARSHMALLOW_MAJOR_VERSION",
)
