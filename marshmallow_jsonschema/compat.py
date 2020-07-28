import marshmallow

MARSHMALLOW_MAJOR_VERSION = int(marshmallow.__version__.split(".", 1)[0])

MARSHMALLOW_2 = MARSHMALLOW_MAJOR_VERSION == 2
MARSHMALLOW_3 = MARSHMALLOW_MAJOR_VERSION == 3

if MARSHMALLOW_2:
    RAISE = "raise"
    INCLUDE = "include"
    EXCLUDE = "exclude"

    def dot_data_backwards_compatible(json_schema):
        return json_schema.data

    def list_inner(list_field):
        return list_field.container


else:
    from marshmallow import RAISE, INCLUDE, EXCLUDE

    def dot_data_backwards_compatible(json_schema):
        return json_schema

    def list_inner(list_field):
        return list_field.inner


__all__ = ("list_inner", "dot_data_backwards_compatible", "MARSHMALLOW_MAJOR_VERSION")
