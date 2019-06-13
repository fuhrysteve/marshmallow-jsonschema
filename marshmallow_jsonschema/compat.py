import sys
import marshmallow

PY2 = int(sys.version_info[0]) == 2

if PY2:
    text_type = unicode
    binary_type = str
    basestring = basestring
else:
    text_type = str
    binary_type = bytes
    basestring = (str, bytes)


if marshmallow.__version__.split('.', 1)[0] >= '3':
    marshmallow_2 = False
    def dot_data_backwards_compatable(json_schema):
        return json_schema
else:
    marshmallow_2 = True
    def dot_data_backwards_compatable(json_schema):
        return json_schema.data


__all__ = (
    'text_type',
    'binary_type',
    'basestring',
    'marshmallow_2',
    'dot_data_backwards_compatable',
)
