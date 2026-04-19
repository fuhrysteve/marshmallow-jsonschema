import datetime
import decimal
import json
import uuid
from enum import Enum
from inspect import isclass, signature
import typing

from importlib.metadata import version as _pkg_version

from marshmallow import fields, missing, Schema, validate
from marshmallow.class_registry import get_class
from marshmallow.decorators import post_dump

from marshmallow import INCLUDE, EXCLUDE, RAISE

# Major-version sniff so callers can branch on m3 vs m4 if they need to.
# Used internally to gate features that the underlying marshmallow
# release no longer provides (Schema(context=...), Schema.context, etc.).
# marshmallow 3 exposed `__version__` directly; marshmallow 4 dropped it,
# so read the installed distribution version instead. Fall back to 3 if
# the metadata isn't present (e.g. a vendored copy with no dist-info).
MARSHMALLOW_MAJOR: int
try:
    MARSHMALLOW_MAJOR = int(_pkg_version("marshmallow").split(".", 1)[0])
except Exception:
    MARSHMALLOW_MAJOR = 3

# marshmallow 3.x exposed the private `_Missing` type on `marshmallow.utils`;
# marshmallow 4.x removed it. Keep the runtime constant for any external
# consumer that imported it from us in the past, but use `typing.Any` in
# our own annotations so mypy is happy on both versions.
_Missing = type(missing)

ALLOW_UNIONS: bool
try:
    from marshmallow_union import Union

    ALLOW_UNIONS = True
except ImportError:
    ALLOW_UNIONS = False

ALLOW_MARSHMALLOW_ENUM: bool
try:
    from marshmallow_enum import EnumField, LoadDumpOptions

    ALLOW_MARSHMALLOW_ENUM = True
except ImportError:
    ALLOW_MARSHMALLOW_ENUM = False

ALLOW_NATIVE_ENUM: bool
try:
    from marshmallow.fields import Enum as NativeEnumField

    ALLOW_NATIVE_ENUM = True
except ImportError:
    ALLOW_NATIVE_ENUM = False

# Backward-compat alias: historically this meant "marshmallow_enum is
# importable", and external code has checked it as such. Keep it pointed
# at the third-party flag so the semantic doesn't shift under callers.
ALLOW_ENUMS: bool = ALLOW_MARSHMALLOW_ENUM

from .exceptions import UnsupportedValueError
from .validation import (
    handle_contains_only,
    handle_equal,
    handle_length,
    handle_one_of,
    handle_range,
    handle_regexp,
)

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
    str: {"type": "string"},
    bytes: {"type": "string"},
    decimal.Decimal: {"type": "number", "format": "decimal"},
    set: {"type": "array"},
    tuple: {"type": "array"},
    float: {"type": "number", "format": "float"},
    int: {"type": "integer"},
    bool: {"type": "boolean"},
    Enum: {"type": "string"},
}

# We use these pairs to get proper python type from marshmallow type.
# We can't use mapping as earlier Python versions might shuffle dict contents
# and then `fields.Number` might end up before `fields.Integer`.
# As we perform sequential subclass check to determine proper Python type,
# we can't let that happen.
MARSHMALLOW_TO_PY_TYPES_PAIRS = [
    # This part of a mapping is carefully selected from marshmallow source code,
    # see marshmallow.BaseSchema.TYPE_MAPPING.
    (fields.UUID, uuid.UUID),
    (fields.String, str),
    (fields.Float, float),
    (fields.Raw, str),
    (fields.Boolean, bool),
    (fields.Integer, int),
    (fields.Time, datetime.time),
    (fields.Date, datetime.date),
    (fields.TimeDelta, datetime.timedelta),
    (fields.DateTime, datetime.datetime),
    (fields.Decimal, decimal.Decimal),
    # These are some mappings that generally make sense for the rest
    # of marshmallow fields.
    (fields.Email, str),
    (fields.Dict, dict),
    (fields.Url, str),
    (fields.List, list),
    (fields.Number, decimal.Decimal),
    (fields.IP, str),
    (fields.IPInterface, str),
    # This one is here just for completeness sake and to check for
    # unknown marshmallow fields more cleanly.
    (fields.Nested, dict),
]

if ALLOW_MARSHMALLOW_ENUM:
    # We currently only support loading enum's from their names. So the possible
    # values will always map to string in the JSONSchema
    MARSHMALLOW_TO_PY_TYPES_PAIRS.append((EnumField, Enum))
if ALLOW_NATIVE_ENUM:
    MARSHMALLOW_TO_PY_TYPES_PAIRS.append((NativeEnumField, Enum))


FIELD_VALIDATORS = {
    validate.ContainsOnly: handle_contains_only,
    validate.Equal: handle_equal,
    validate.Length: handle_length,
    validate.OneOf: handle_one_of,
    validate.Range: handle_range,
    validate.Regexp: handle_regexp,
}


def _is_json_serializable(value) -> bool:
    """Return True if `value` can be emitted into a JSON schema directly.

    Used to guard `default` emission: marshmallow accepts Python objects
    (UUID, datetime, etc.) as dump_default values, but those objects can
    only be serialized by marshmallow's own field-specific logic - they
    aren't valid JSON literals, so including them as `default` produces
    a schema that can't round-trip through `json.dumps`.
    """
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def _resolve_additional_properties(cls) -> bool:
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


def _resolve_schema_meta_string(cls, name):
    """Read a string option off ``cls.Meta`` and validate it. Returns None
    when the option isn't set. Raises ``UnsupportedValueError`` if present
    but not a str, so callers get a clear error instead of a silently
    malformed schema."""
    value = getattr(cls.Meta, name, None)
    if value is None:
        return None
    if not isinstance(value, str):
        raise UnsupportedValueError("`{}` must be a str".format(name))
    return value


class JSONSchema(Schema):
    """Converts to JSONSchema as defined by http://json-schema.org/."""

    properties = fields.Method("get_properties")
    type = fields.Constant("object")
    required = fields.Method("get_required")

    def __init__(self, *args, **kwargs) -> None:
        """Setup internal cache of nested fields, to prevent recursion.

        :param bool props_ordered: if `True` order of properties will be save as declare in class,
                                   else will using sorting, default is `False`.
                                   Note: For the marshmallow scheme, also need to enable
                                   ordering of fields too (via `class Meta`, attribute `ordered`).
        :param str definitions_path: name of the top-level dict key holding nested
                                     schema definitions and the JSON pointer segment
                                     used in $ref strings. Default is `"definitions"`.
                                     Must be a single segment (no `/`); rejected with
                                     `UnsupportedValueError` otherwise.
        """
        self._nested_schema_classes: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        self.nested = kwargs.pop("nested", False)
        self.props_ordered = kwargs.pop("props_ordered", False)
        self.definitions_path = kwargs.pop("definitions_path", "definitions")
        # `definitions_path` ends up both as a JSON-pointer segment in $ref
        # strings AND as a top-level dict key in the output. Validate it
        # up-front so we surface a clear error instead of a confusing
        # downstream crash:
        #  - must be a non-empty str (rules out None / int / "")
        #  - must be a single segment (multi-segment paths like
        #    "components/schemas" produce a flat dict key with a slash in
        #    it rather than the nested structure consumers expect)
        if not isinstance(self.definitions_path, str) or not self.definitions_path:
            raise UnsupportedValueError(
                "`definitions_path` must be a non-empty str (got %r)"
                % (self.definitions_path,)
            )
        if "/" in self.definitions_path:
            raise UnsupportedValueError(
                "`definitions_path` must be a single segment (got "
                "%r); nested paths require post-processing the output."
                % self.definitions_path
            )
        setattr(self.opts, "ordered", self.props_ordered)
        super().__init__(*args, **kwargs)

    def get_properties(self, obj) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        """Fill out properties field."""
        properties = self.dict_class()

        if self.props_ordered:
            fields_items_sequence = obj.fields.items()
        else:
            if callable(obj):
                fields_items_sequence = sorted(obj().fields.items())
            else:
                fields_items_sequence = sorted(obj.fields.items())

        for field_name, field in fields_items_sequence:
            schema = self._get_schema_for_field(obj, field)
            properties[field.metadata.get("name") or field.data_key or field.name] = (
                schema
            )

        return properties

    def get_required(self, obj) -> typing.Union[typing.List[str], typing.Any]:
        """Fill out required field."""
        required = []
        if callable(obj):
            field_items_iterable = sorted(obj().fields.items())
        else:
            field_items_iterable = sorted(obj.fields.items())
        for field_name, field in field_items_iterable:
            if field.required:
                required.append(field.data_key or field.name)

        return required or missing

    def _from_python_type(self, obj, field, pytype) -> typing.Dict[str, typing.Any]:
        """Get schema definition from python type."""
        json_schema = {"title": field.attribute or field.name or ""}

        for key, val in PY_TO_JSON_TYPES_MAP[pytype].items():
            json_schema[key] = val

        if field.dump_only:
            json_schema["readOnly"] = True

        if field.dump_default is not missing and not callable(field.dump_default):
            if _is_json_serializable(field.dump_default):
                json_schema["default"] = field.dump_default

        if ALLOW_NATIVE_ENUM and isinstance(field, NativeEnumField):
            json_schema["enum"] = self._get_native_enum_values(field)
        elif ALLOW_MARSHMALLOW_ENUM and isinstance(field, EnumField):
            json_schema["enum"] = self._get_enum_values(field)

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
            json_schema["items"] = self._get_schema_for_field(obj, field.inner)

        if isinstance(field, fields.Dict):
            json_schema["additionalProperties"] = (
                self._get_schema_for_field(obj, field.value_field)
                if field.value_field
                else {}
            )
        return json_schema

    def _get_enum_values(self, field) -> typing.List[str]:
        assert ALLOW_MARSHMALLOW_ENUM and isinstance(field, EnumField)

        if field.load_by == LoadDumpOptions.value:
            # Python allows enum values to be almost anything, so it's easier to just load from the
            # names of the enum's which will have to be strings.
            raise NotImplementedError(
                "Currently do not support JSON schema for enums loaded by value"
            )

        return [value.name for value in field.enum]

    def _get_native_enum_values(self, field) -> typing.List[str]:
        assert ALLOW_NATIVE_ENUM and isinstance(field, NativeEnumField)

        if field.by_value:
            # Python allows enum values to be almost anything, so it's easier to just load from the
            # names of the enum's which will have to be strings.
            raise NotImplementedError(
                "Currently do not support JSON schema for enums loaded by value"
            )

        return [value.name for value in field.enum]

    def _from_union_schema(
        self, obj, field
    ) -> typing.Dict[str, typing.List[typing.Any]]:
        """Get a union type schema. Uses anyOf to allow the value to be any of the provided sub fields"""
        assert ALLOW_UNIONS and isinstance(field, Union)

        return {
            "anyOf": [
                self._get_schema_for_field(obj, sub_field)
                for sub_field in field._candidate_fields
            ]
        }

    def _wrap_allow_none(self, schema, field):
        """If ``field.allow_none`` is set, wrap the schema in
        ``anyOf: [<schema>, {"type": "null"}]``. Returns the new schema
        (or the original if allow_none is False). Mirrors
        ``_from_nested_schema``'s allow_none handling so the new
        Tuple / Constant / Pluck handlers stay consistent with it."""
        if field.allow_none:
            return {"anyOf": [schema, {"type": "null"}]}
        return schema

    def _from_tuple_field(self, obj, field):
        """`fields.Tuple([Inner1(), Inner2(), ...])` is a fixed-length
        positional sequence; we emit Draft-7's array form with a
        positional `items` schema list and `min/maxItems` pinning the
        length so a JSON Schema validator rejects wrong-arity inputs.
        """
        item_schemas = [
            self._get_schema_for_field(obj, sub) for sub in field.tuple_fields
        ]
        schema = {
            "type": "array",
            "items": item_schemas,
            "minItems": len(item_schemas),
            "maxItems": len(item_schemas),
        }
        # Apply the outer Tuple field's metadata / dump_only / dump_default
        # so callers can attach a title or description like they would on
        # any other field type.
        self._apply_custom_field_attributes(schema, field)
        return self._wrap_allow_none(schema, field)

    def _from_constant_field(self, obj, field):
        """`fields.Constant(value)` always serializes to a fixed value;
        emit JSON Schema's `const`. Also try to emit a matching `type`
        when the constant maps cleanly to one of our known Python -> JSON
        type pairs - some validators are happier with both."""
        schema: typing.Dict[str, typing.Any] = {}
        if _is_json_serializable(field.constant):
            schema["const"] = field.constant
        py_type = type(field.constant)
        if py_type in PY_TO_JSON_TYPES_MAP:
            for key, val in PY_TO_JSON_TYPES_MAP[py_type].items():
                schema[key] = val
        # Apply the field's metadata / dump_only so callers can attach a
        # title or description.
        self._apply_custom_field_attributes(schema, field)
        # `fields.Constant` sets `dump_default = constant` internally,
        # so the metadata pass would emit a `default` matching the
        # `const` we already wrote. Strip the redundant key.
        if "const" in schema and schema.get("default") == schema["const"]:
            schema.pop("default", None)
        return self._wrap_allow_none(schema, field)

    def _from_pluck_field(self, obj, field):
        """`fields.Pluck(NestedSchema, "x")` extracts a single field from
        a nested schema. We emit the picked field's schema directly,
        not a `$ref` to the whole nested definition - otherwise the
        emitted shape would describe the wrong type entirely.
        """
        nested = field.nested
        if isinstance(nested, (str, bytes)):
            nested = get_class(nested)
        if isclass(nested) and issubclass(nested, Schema):
            try:
                nested_instance = nested(context=obj.context)
            except (AttributeError, TypeError):
                nested_instance = nested()
        elif callable(nested):
            nested_instance = nested()
        else:
            nested_instance = nested

        picked = nested_instance.fields[field.field_name]
        schema = self._get_schema_for_field(obj, picked)

        # Overlay outer Pluck-field attributes (metadata, dump_default,
        # dump_only) on top of the picked field's schema. Users who set
        # these on a Pluck field are describing the OUTER reference, so
        # direct assignment (rather than setdefault) is the right
        # precedence here - the outer description wins over whatever the
        # inner picked field happened to derive automatically.
        if field.dump_only:
            schema["readOnly"] = True
        if field.dump_default is not missing and not callable(field.dump_default):
            if _is_json_serializable(field.dump_default):
                schema["default"] = field.dump_default
        metadata = field.metadata.get("metadata", {})
        metadata.update(field.metadata)
        for md_key, md_val in metadata.items():
            if md_key in ("metadata", "name"):
                continue
            schema[md_key] = md_val

        schema = self._wrap_allow_none(schema, field)

        if field.many:
            # Match `_from_nested_schema`'s many-handling: an optional
            # many-array can also be null, while a required one must be
            # an array.
            schema = {
                "type": "array" if field.required else ["array", "null"],
                "items": schema,
            }
        return schema

    def _get_python_type(self, field):
        """Get python type based on field subclass"""
        for map_class, pytype in MARSHMALLOW_TO_PY_TYPES_PAIRS:
            if issubclass(field.__class__, map_class):
                return pytype

        raise UnsupportedValueError(
            "Cannot derive a JSON Schema type for field "
            "%s (class %s). To support a custom field, either "
            "subclass an existing marshmallow field type "
            "(e.g. `class MyField(fields.String): ...`) or add a "
            "`_jsonschema_type_mapping(self)` method to the field "
            'returning a JSON Schema dict like `{"type": "string"}`.'
            % (getattr(field, "name", "<unnamed>"), type(field).__name__)
        )

    def _call_jsonschema_type_mapping(self, obj, field):
        """Invoke the field's ``_jsonschema_type_mapping``, optionally passing
        through the JSONSchema instance and the schema obj.

        Existing no-arg implementations continue to work unchanged. Custom
        field types that explicitly declare extra parameters can introspect
        ``self`` to call back into the JSONSchema machinery - useful for
        wrapper-style fields that need to emit a $ref to a recursive schema.
        """
        mapping = field._jsonschema_type_mapping
        # len(sig.parameters) excludes `self` because we're looking at the
        # bound method's signature.
        if len(signature(mapping).parameters) == 2:
            return mapping(self, obj)
        return mapping()

    def _apply_custom_field_attributes(self, schema, field):
        """Apply field-level attributes (title/description metadata, default,
        dump_only) to a schema produced by a ``_jsonschema_type_mapping``.

        `_from_python_type` applies these itself; custom-typed fields bypass
        that path, so without this they'd silently lose their metadata.
        """
        if field.dump_only:
            schema["readOnly"] = True

        if field.dump_default is not missing and not callable(field.dump_default):
            if _is_json_serializable(field.dump_default):
                schema["default"] = field.dump_default

        # NOTE: doubled up to maintain backwards compatibility
        metadata = field.metadata.get("metadata", {})
        metadata.update(field.metadata)
        for md_key, md_val in metadata.items():
            if md_key in ("metadata", "name", "_jsonschema_type_mapping"):
                continue
            schema.setdefault(md_key, md_val)

    def _get_schema_for_field(self, obj, field):
        """Get schema and validators for field."""
        if hasattr(field, "_jsonschema_type_mapping"):
            schema = self._call_jsonschema_type_mapping(obj, field)
            self._apply_custom_field_attributes(schema, field)
        elif "_jsonschema_type_mapping" in field.metadata:
            schema = field.metadata["_jsonschema_type_mapping"]
            self._apply_custom_field_attributes(schema, field)
        else:
            # Pluck is a Nested subclass, so it must be checked first.
            if isinstance(field, fields.Pluck):
                schema = self._from_pluck_field(obj, field)
            elif isinstance(field, fields.Nested):
                # Special treatment for nested fields.
                schema = self._from_nested_schema(obj, field)
            elif hasattr(fields, "Tuple") and isinstance(field, fields.Tuple):
                # `fields.Tuple` was added in marshmallow 3.16; the
                # hasattr guard keeps us importable on 3.13-3.15.
                schema = self._from_tuple_field(obj, field)
            elif isinstance(field, fields.Constant):
                schema = self._from_constant_field(obj, field)
            elif ALLOW_UNIONS and isinstance(field, Union):
                schema = self._from_union_schema(obj, field)
            else:
                pytype = self._get_python_type(field)
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
        if isinstance(field.nested, (str, bytes)):
            nested = get_class(field.nested)
        else:
            nested = field.nested

        if isclass(nested) and issubclass(nested, Schema):
            name = nested.__name__
            only = field.only
            exclude = field.exclude
            nested_cls = nested
            # marshmallow 3 accepts `context` as a constructor kwarg and
            # exposes it as a Schema attribute; marshmallow 4 removed both
            # in favor of `contextvars.ContextVar`. Forward context on m3
            # where possible and fall back gracefully on m4.
            try:
                nested_instance = nested(
                    only=only, exclude=exclude, context=obj.context
                )
            except (AttributeError, TypeError):
                nested_instance = nested(only=only, exclude=exclude)
        elif callable(nested):
            nested_instance = nested()
            nested_type = type(nested_instance)
            name = nested_type.__name__
            nested_cls = nested_type.__class__
        else:
            nested_cls = nested.__class__
            name = nested_cls.__name__
            nested_instance = nested

        outer_name = obj.__class__.__name__
        # If this is not a schema we've seen, and it's not this schema (checking this for recursive schemas),
        # put it in our list of schema defs
        if name not in self._nested_schema_classes and name != outer_name:
            wrapped_nested = self.__class__(
                nested=True,
                props_ordered=self.props_ordered,
                definitions_path=self.definitions_path,
            )
            wrapped_dumped = wrapped_nested.dump(nested_instance)

            wrapped_dumped["additionalProperties"] = _resolve_additional_properties(
                nested_cls
            )
            for meta_key in ("title", "description"):
                value = _resolve_schema_meta_string(nested_cls, meta_key)
                if value is not None:
                    wrapped_dumped[meta_key] = value

            self._nested_schema_classes[name] = wrapped_dumped

            self._nested_schema_classes.update(wrapped_nested._nested_schema_classes)

        # and the schema is just a reference to the def
        schema = self._schema_base(name)

        # NOTE: doubled up to maintain backwards compatibility
        metadata = field.metadata.get("metadata", {})
        metadata.update(field.metadata)

        for md_key, md_val in metadata.items():
            if md_key in ("metadata", "name"):
                continue
            schema[md_key] = md_val

        if field.dump_default is not missing and not callable(field.dump_default):
            schema["default"] = nested_instance.dump(field.dump_default)

        if field.allow_none:
            schema = {"anyOf": [schema, {"type": "null"}]}

        if field.many:
            schema = {
                "type": "array" if field.required else ["array", "null"],
                "items": schema,
            }

        return schema

    def _schema_base(self, name):
        return {
            "type": "object",
            "$ref": "#/{}/{}".format(self.definitions_path, name),
        }

    def dump(self, obj, **kwargs) -> typing.Dict[str, typing.Any]:
        """Render `obj` as a JSON Schema dict.

        Narrower return type than the base `Schema.dump`'s
        `dict | list | None` because `JSONSchema` always wraps the
        output in a single root dict (`$schema` + `definitions` +
        `$ref`).
        """
        self.obj = obj
        return super().dump(obj, **kwargs)

    @post_dump
    def wrap(self, data, **_) -> typing.Dict[str, typing.Any]:
        """Wrap this with the root schema definitions."""
        if self.nested:  # no need to wrap, will be in outer defs
            return data

        cls = self.obj.__class__
        name = cls.__name__

        data["additionalProperties"] = _resolve_additional_properties(cls)
        for meta_key in ("title", "description"):
            value = _resolve_schema_meta_string(cls, meta_key)
            if value is not None:
                data[meta_key] = value

        self._nested_schema_classes[name] = data
        root = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            self.definitions_path: self._nested_schema_classes,
            "$ref": "#/{path}/{name}".format(path=self.definitions_path, name=name),
        }
        return root
