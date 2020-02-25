import datetime
import decimal
import uuid
from inspect import isclass

from marshmallow import fields, missing, Schema, validate
from marshmallow.class_registry import get_class
from marshmallow.decorators import post_dump

from .compat import (
    text_type,
    binary_type,
    basestring,
    dot_data_backwards_compatible,
    list_inner,
    INCLUDE,
    EXCLUDE,
    RAISE,
)
from .exceptions import UnsupportedValueError
from .validation import handle_length, handle_one_of, handle_range, handle_regexp

__all__ = ("JSONSchema",)

PY_TO_JSON_TYPES_MAP = {
    dict: {"type": "object"},
    list: {"type": "array"},
    datetime.time: {"type": "string", "format": "time"},
    datetime.timedelta: {
        # TODO explore using 'range'?
        "type": "string"
    },
    datetime.datetime: {"type": "string", "format": "date-time"},
    datetime.date: {"type": "string", "format": "date"},
    uuid.UUID: {"type": "string", "format": "uuid"},
    text_type: {"type": "string"},
    binary_type: {"type": "string"},
    decimal.Decimal: {"type": "number", "format": "decimal"},
    set: {"type": "array"},
    tuple: {"type": "array"},
    float: {"type": "number", "format": "float"},
    int: {"type": "number", "format": "integer"},
    bool: {"type": "boolean"},
}

# We use these pairs to get proper python type from marshmallow type.
# We can't use mapping as earlier Python versions might shuffle dict contents
# and then `fields.Number` might end up before `fields.Integer`.
# As we perform sequential subclass check to determine proper Python type,
# we can't let that happen.
MARSHMALLOW_TO_PY_TYPES_PAIRS = (
    # This part of a mapping is carefully selected from marshmallow source code,
    # see marshmallow.BaseSchema.TYPE_MAPPING.
    (fields.String, text_type),
    (fields.Float, float),
    (fields.Raw, text_type),
    (fields.Boolean, bool),
    (fields.Integer, int),
    (fields.UUID, uuid.UUID),
    (fields.Time, datetime.time),
    (fields.Date, datetime.date),
    (fields.TimeDelta, datetime.timedelta),
    (fields.DateTime, datetime.datetime),
    (fields.Decimal, decimal.Decimal),
    # These are some mappings that generally make sense for the rest
    # of marshmallow fields.
    (fields.Email, text_type),
    (fields.Dict, dict),
    (fields.Url, text_type),
    (fields.List, list),
    (fields.Number, decimal.Decimal),
    # This one is here just for completeness sake and to check for
    # unknown marshmallow fields more cleanly.
    (fields.Nested, dict),
)

FIELD_VALIDATORS = {
    validate.Length: handle_length,
    validate.OneOf: handle_one_of,
    validate.Range: handle_range,
    validate.Regexp: handle_regexp,
}


def _resolve_additional_properties(cls):
    meta = cls.Meta

    additional_properties = getattr(meta, "additional_properties", None)
    if additional_properties is not None:
        if additional_properties in (True, False):
            return additional_properties
        else:
            raise UnsupportedValueError(
                "`additional_properties` must be either True or False"
            )

    unknown = getattr(meta, "unknown", None)
    if unknown is None:
        return False
    elif unknown in (RAISE, EXCLUDE):
        return False
    elif unknown == INCLUDE:
        return True
    else:
        raise UnsupportedValueError("Unknown value %s for `unknown`" % unknown)


class JSONSchema(Schema):
    """Converts to JSONSchema as defined by http://json-schema.org/."""

    properties = fields.Method("get_properties")
    type = fields.Constant("object")
    required = fields.Method("get_required")

    def __init__(self, *args, **kwargs):
        """Setup internal cache of nested fields, to prevent recursion.

        :param bool props_ordered: if `True` order of properties will be save as declare in class,
                                   else will using sorting, default is `False`.
                                   Note: For the marshmallow scheme, also need to enable
                                   ordering of fields too (via `class Meta`, attribute `ordered`).
        """
        self._nested_schema_classes = {}
        self.nested = kwargs.pop("nested", False)
        self.props_ordered = kwargs.pop("props_ordered", False)
        setattr(self.opts, "ordered", self.props_ordered)
        super(JSONSchema, self).__init__(*args, **kwargs)

    def get_properties(self, obj):
        """Fill out properties field."""
        properties = self.dict_class()

        if self.props_ordered:
            fields_items_sequence = obj.fields.items()
        else:
            fields_items_sequence = sorted(obj.fields.items())

        for field_name, field in fields_items_sequence:
            schema = self._get_schema_for_field(obj, field)
            properties[field.metadata.get("name") or field.name] = schema

        return properties

    def get_required(self, obj):
        """Fill out required field."""
        required = []

        for field_name, field in sorted(obj.fields.items()):
            if field.required:
                required.append(field.name)

        return required or missing

    def _from_python_type(self, obj, field, pytype):
        """Get schema definition from python type."""
        json_schema = {"title": field.attribute or field.name}

        for key, val in PY_TO_JSON_TYPES_MAP[pytype].items():
            json_schema[key] = val

        if field.dump_only:
            json_schema["readonly"] = True

        if field.default is not missing:
            json_schema["default"] = field.default

        if field.allow_none:
            previous_type = json_schema["type"]
            json_schema["type"] = [previous_type, "null"]

        # NOTE: doubled up to maintain backwards compatibility
        metadata = field.metadata.get("metadata", {})
        metadata.update(field.metadata)

        for md_key, md_val in metadata.items():
            if md_key in ("metadata", "name"):
                continue
            json_schema[md_key] = md_val

        if isinstance(field, fields.List):
            json_schema["items"] = self._get_schema_for_field(obj, list_inner(field))
        return json_schema

    def _get_python_type(self, field):
        """Get python type based on field subclass"""
        for map_class, pytype in MARSHMALLOW_TO_PY_TYPES_PAIRS:
            if issubclass(field.__class__, map_class):
                return pytype

        raise UnsupportedValueError("unsupported field type %s" % field)

    def _get_schema_for_field(self, obj, field):
        """Get schema and validators for field."""
        if hasattr(field, "_jsonschema_type_mapping"):
            schema = field._jsonschema_type_mapping()
        elif "_jsonschema_type_mapping" in field.metadata:
            schema = field.metadata["_jsonschema_type_mapping"]
        else:
            pytype = self._get_python_type(field)
            if isinstance(field, fields.Nested):
                # Special treatment for nested fields.
                schema = self._from_nested_schema(obj, field)
            else:
                schema = self._from_python_type(obj, field, pytype)
        # Apply any and all validators that field may have
        for validator in field.validators:
            if validator.__class__ in FIELD_VALIDATORS:
                schema = FIELD_VALIDATORS[validator.__class__](
                    schema, field, validator, obj
                )
            else:
                base_class = getattr(
                    validator, "_jsonschema_base_validator_class", None
                )
                if base_class is not None and base_class in FIELD_VALIDATORS:
                    schema = FIELD_VALIDATORS[base_class](schema, field, validator, obj)
        return schema

    def _from_nested_schema(self, obj, field):
        """Support nested field."""
        if isinstance(field.nested, basestring):
            nested = get_class(field.nested)
        else:
            nested = field.nested

        if isclass(nested) and issubclass(nested, Schema):
            name = nested.__name__
            only = field.only
            exclude = field.exclude
            nested_cls = nested
            nested_instance = nested(only=only, exclude=exclude)
        else:
            nested_cls = nested.__class__
            name = nested_cls.__name__
            nested_instance = nested

        outer_name = obj.__class__.__name__
        # If this is not a schema we've seen, and it's not this schema (checking this for recursive schemas),
        # put it in our list of schema defs
        if name not in self._nested_schema_classes and name != outer_name:
            wrapped_nested = self.__class__(nested=True)
            wrapped_dumped = dot_data_backwards_compatible(
                wrapped_nested.dump(nested_instance)
            )

            wrapped_dumped["additionalProperties"] = _resolve_additional_properties(
                nested_cls
            )

            self._nested_schema_classes[name] = wrapped_dumped

            self._nested_schema_classes.update(wrapped_nested._nested_schema_classes)

        # and the schema is just a reference to the def
        schema = {"type": "object", "$ref": "#/definitions/{}".format(name)}

        # NOTE: doubled up to maintain backwards compatibility
        metadata = field.metadata.get("metadata", {})
        metadata.update(field.metadata)

        for md_key, md_val in metadata.items():
            if md_key in ("metadata", "name"):
                continue
            schema[md_key] = md_val

        if field.many:
            schema = {
                "type": "array" if field.required else ["array", "null"],
                "items": schema,
            }

        return schema

    def dump(self, obj, **kwargs):
        """Take obj for later use: using class name to namespace definition."""
        self.obj = obj
        return super(JSONSchema, self).dump(obj, **kwargs)

    @post_dump
    def wrap(self, data, **_):
        """Wrap this with the root schema definitions."""
        if self.nested:  # no need to wrap, will be in outer defs
            return data

        cls = self.obj.__class__
        name = cls.__name__

        data["additionalProperties"] = _resolve_additional_properties(cls)

        self._nested_schema_classes[name] = data
        root = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": self._nested_schema_classes,
            "$ref": "#/definitions/{name}".format(name=name),
        }
        return root
