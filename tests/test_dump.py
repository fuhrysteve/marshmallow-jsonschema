import uuid
from enum import Enum

import jsonschema
import pytest
from marshmallow import Schema, fields, validate
from marshmallow_enum import EnumField
from marshmallow_union import Union

from marshmallow_jsonschema import JSONSchema, UnsupportedValueError
from marshmallow_jsonschema.base import ALLOW_NATIVE_ENUM, MARSHMALLOW_MAJOR
from . import UserSchema, validate_and_dump

if ALLOW_NATIVE_ENUM:
    from marshmallow.fields import Enum as NativeEnumField


def test_dump_schema():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    assert len(schema.fields) > 1

    props = dumped["definitions"]["UserSchema"]["properties"]
    for field_name, field in schema.fields.items():
        assert field_name in props


def test_default():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["UserSchema"]["properties"]
    assert props["id"]["default"] == "no-id"


def test_default_nonserializable_not_emitted():
    """A non-callable dump_default whose Python value isn't JSON-serializable
    must not be emitted. Otherwise the schema dict can't round-trip through
    `json.dumps`. Regression for #181."""
    import json

    class TestSchema(Schema):
        uid = fields.UUID(dump_default=uuid.uuid4())

    dumped = validate_and_dump(TestSchema())

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert "default" not in props["uid"]
    json.dumps(dumped)


def test_default_callable_not_serialized():
    class TestSchema(Schema):
        uid = fields.UUID(dump_default=uuid.uuid4)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert "default" not in props["uid"]


def test_uuid():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["UserSchema"]["properties"]
    assert props["uid"]["type"] == "string"
    assert props["uid"]["format"] == "uuid"


def test_metadata():
    """Metadata should be available in the field definition."""

    class TestSchema(Schema):
        myfield = fields.String(metadata={"foo": "Bar"})
        yourfield = fields.Integer(required=True, metadata={"baz": "waz"})

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["myfield"]["foo"] == "Bar"
    assert props["yourfield"]["baz"] == "waz"
    assert "metadata" not in props["myfield"]
    assert "metadata" not in props["yourfield"]

    # repeat process to assert idempotency
    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["myfield"]["foo"] == "Bar"
    assert props["yourfield"]["baz"] == "waz"


def test_descriptions():
    class TestSchema(Schema):
        myfield = fields.String(metadata={"description": "Brown Cow"})
        yourfield = fields.Integer(required=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["myfield"]["description"] == "Brown Cow"


def test_nested_descriptions():
    class TestNestedSchema(Schema):
        myfield = fields.String(metadata={"description": "Brown Cow"})
        yourfield = fields.Integer(required=True)

    class TestSchema(Schema):
        nested = fields.Nested(
            TestNestedSchema, metadata={"description": "Nested 1", "title": "Title1"}
        )
        yourfield_nested = fields.Integer(required=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    nested_def = dumped["definitions"]["TestNestedSchema"]
    nested_dmp = dumped["definitions"]["TestSchema"]["properties"]["nested"]
    assert nested_def["properties"]["myfield"]["description"] == "Brown Cow"

    assert nested_dmp["$ref"] == "#/definitions/TestNestedSchema"
    assert nested_dmp["description"] == "Nested 1"
    assert nested_dmp["title"] == "Title1"


def test_nested_string_to_cls():
    class TestNamedNestedSchema(Schema):
        foo = fields.Integer(required=True)

    class TestSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested("TestNamedNestedSchema")

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    nested_def = dumped["definitions"]["TestNamedNestedSchema"]
    nested_dmp = dumped["definitions"]["TestSchema"]["properties"]["nested"]
    assert nested_dmp["type"] == "object"
    assert nested_def["properties"]["foo"]["type"] == "integer"


@pytest.mark.skipif(
    MARSHMALLOW_MAJOR >= 4,
    reason="`Schema(context=...)` was removed in marshmallow 4 in favor of contextvars",
)
def test_nested_context():
    class TestNestedSchema(Schema):
        def __init__(self, *args, **kwargs):
            if kwargs.get("context", {}).get("hide", False):
                kwargs["exclude"] = ["foo"]
            super().__init__(*args, **kwargs)

        foo = fields.Integer(required=True)
        bar = fields.Integer(required=True)

    class TestSchema(Schema):
        bar = fields.Nested(TestNestedSchema)

    schema = TestSchema()
    dumped_show = validate_and_dump(schema)

    schema = TestSchema(context={"hide": True})
    dumped_hide = validate_and_dump(schema)

    nested_show = dumped_show["definitions"]["TestNestedSchema"]["properties"]
    nested_hide = dumped_hide["definitions"]["TestNestedSchema"]["properties"]

    assert "bar" in nested_show and "foo" in nested_show
    assert "bar" in nested_hide and "foo" not in nested_hide


def test_list():
    class ListSchema(Schema):
        foo = fields.List(fields.String(), required=True)

    schema = ListSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["definitions"]["ListSchema"]["properties"]["foo"]
    assert nested_json["type"] == "array"
    assert "items" in nested_json

    item_schema = nested_json["items"]
    assert item_schema["type"] == "string"


def test_list_nested():
    """Test that a list field will work with an inner nested field."""

    class InnerSchema(Schema):
        foo = fields.Integer(required=True)

    class ListSchema(Schema):
        bar = fields.List(fields.Nested(InnerSchema), required=True)

    schema = ListSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["definitions"]["ListSchema"]["properties"]["bar"]

    assert nested_json["type"] == "array"
    assert "items" in nested_json

    item_schema = nested_json["items"]
    assert "InnerSchema" in item_schema["$ref"]


def test_dict():
    class DictSchema(Schema):
        foo = fields.Dict()

    schema = DictSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["definitions"]["DictSchema"]["properties"]["foo"]

    assert nested_json["type"] == "object"
    assert "additionalProperties" in nested_json

    item_schema = nested_json["additionalProperties"]
    assert item_schema == {}


def test_dict_with_value_field():
    class DictSchema(Schema):
        foo = fields.Dict(keys=fields.String, values=fields.Integer)

    schema = DictSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["definitions"]["DictSchema"]["properties"]["foo"]

    assert nested_json["type"] == "object"
    assert "additionalProperties" in nested_json

    item_schema = nested_json["additionalProperties"]
    assert item_schema["type"] == "integer"


def test_dict_with_nested_value_field():
    class InnerSchema(Schema):
        foo = fields.Integer(required=True)

    class DictSchema(Schema):
        bar = fields.Dict(keys=fields.String, values=fields.Nested(InnerSchema))

    schema = DictSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["definitions"]["DictSchema"]["properties"]["bar"]

    assert nested_json["type"] == "object"
    assert "additionalProperties" in nested_json

    item_schema = nested_json["additionalProperties"]
    assert item_schema["type"] == "object"

    assert "InnerSchema" in item_schema["$ref"]


def test_deep_nested():
    """Test that deep nested schemas are in definitions."""

    class InnerSchema(Schema):
        boz = fields.Integer(required=True)

    class InnerMiddleSchema(Schema):
        baz = fields.Nested(InnerSchema, required=True)

    class OuterMiddleSchema(Schema):
        bar = fields.Nested(InnerMiddleSchema, required=True)

    class OuterSchema(Schema):
        foo = fields.Nested(OuterMiddleSchema, required=True)

    schema = OuterSchema()
    dumped = validate_and_dump(schema)

    defs = dumped["definitions"]
    assert "OuterSchema" in defs
    assert "OuterMiddleSchema" in defs
    assert "InnerMiddleSchema" in defs
    assert "InnerSchema" in defs


def test_respect_only_for_nested_schema():
    """Should ignore fields not in 'only' metadata for nested schemas."""

    class InnerRecursiveSchema(Schema):
        id = fields.Integer(required=True)
        baz = fields.String()
        recursive = fields.Nested("InnerRecursiveSchema")

    class MiddleSchema(Schema):
        id = fields.Integer(required=True)
        bar = fields.String()
        inner = fields.Nested("InnerRecursiveSchema", only=("id", "baz"))

    class OuterSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested("MiddleSchema")

    schema = OuterSchema()
    dumped = validate_and_dump(schema)
    inner_props = dumped["definitions"]["InnerRecursiveSchema"]["properties"]
    assert "recursive" not in inner_props


def test_respect_exclude_for_nested_schema():
    """Should ignore fields in 'exclude' metadata for nested schemas."""

    class InnerRecursiveSchema(Schema):
        id = fields.Integer(required=True)
        baz = fields.String()
        recursive = fields.Nested("InnerRecursiveSchema")

    class MiddleSchema(Schema):
        id = fields.Integer(required=True)
        bar = fields.String()
        inner = fields.Nested("InnerRecursiveSchema", exclude=("recursive",))

    class OuterSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested("MiddleSchema")

    schema = OuterSchema()

    dumped = validate_and_dump(schema)

    inner_props = dumped["definitions"]["InnerRecursiveSchema"]["properties"]
    assert "recursive" not in inner_props


def test_respect_dotted_exclude_for_nested_schema():
    """Should ignore dotted fields in 'exclude' metadata for nested schemas."""

    class InnerRecursiveSchema(Schema):
        id = fields.Integer(required=True)
        baz = fields.String()
        recursive = fields.Nested("InnerRecursiveSchema")

    class MiddleSchema(Schema):
        id = fields.Integer(required=True)
        bar = fields.String()
        inner = fields.Nested("InnerRecursiveSchema")

    class OuterSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested("MiddleSchema", exclude=("inner.recursive",))

    schema = OuterSchema()

    dumped = validate_and_dump(schema)

    inner_props = dumped["definitions"]["InnerRecursiveSchema"]["properties"]
    assert "recursive" not in inner_props


def test_respect_default_for_nested_schema():
    class TestNestedSchema(Schema):
        myfield = fields.String()
        yourfield = fields.Integer(required=True)

    nested_default = {"myfield": "myval", "yourfield": 1}

    class TestSchema(Schema):
        nested = fields.Nested(
            TestNestedSchema,
            dump_default=nested_default,
        )
        yourfield_nested = fields.Integer(required=True)

    schema = TestSchema()
    dumped = validate_and_dump(schema)
    default = dumped["definitions"]["TestSchema"]["properties"]["nested"]["default"]
    assert default == nested_default


def test_nested_instance():
    """Should also work with nested schema instances"""

    class TestNestedSchema(Schema):
        baz = fields.Integer()

    class TestSchema(Schema):
        foo = fields.String()
        bar = fields.Nested(TestNestedSchema())

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    nested_def = dumped["definitions"]["TestNestedSchema"]
    nested_obj = dumped["definitions"]["TestSchema"]["properties"]["bar"]

    assert "baz" in nested_def["properties"]
    assert nested_obj["$ref"] == "#/definitions/TestNestedSchema"


def test_function():
    """Function fields can be serialised if type is given."""

    class FnSchema(Schema):
        fn_str = fields.Function(
            lambda: "string",
            required=True,
            metadata={"_jsonschema_type_mapping": {"type": "string"}},
        )
        fn_int = fields.Function(
            lambda: 123,
            required=True,
            metadata={"_jsonschema_type_mapping": {"type": "number"}},
        )

    schema = FnSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["FnSchema"]["properties"]
    assert props["fn_int"]["type"] == "number"
    assert props["fn_str"]["type"] == "string"


def test_nested_recursive():
    """A self-referential schema should not cause an infinite recurse."""

    class RecursiveSchema(Schema):
        foo = fields.Integer(required=True)
        children = fields.Nested("RecursiveSchema", many=True)

    schema = RecursiveSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["RecursiveSchema"]["properties"]
    assert "RecursiveSchema" in props["children"]["items"]["$ref"]


def test_title():
    class TestSchema(Schema):
        myfield = fields.String(metadata={"title": "Brown Cowzz"})
        yourfield = fields.Integer(required=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert (
        dumped["definitions"]["TestSchema"]["properties"]["myfield"]["title"]
        == "Brown Cowzz"
    )


def test_unknown_typed_field_throws_valueerror():
    class Invalid(fields.Field):
        def _serialize(self, value, attr, obj):
            return value

    class UserSchemaWithInvalid(Schema):
        favourite_colour = Invalid()

    schema = UserSchemaWithInvalid()

    with pytest.raises(UnsupportedValueError):
        validate_and_dump(schema)


def test_unknown_typed_field():
    class Colour(fields.Field):
        def _jsonschema_type_mapping(self):
            return {"type": "string"}

        def _serialize(self, value, attr, obj):
            r, g, b = value
            r = hex(r)[2:]
            g = hex(g)[2:]
            b = hex(b)[2:]
            return "#" + r + g + b

    class UserSchema(Schema):
        name = fields.String(required=True)
        favourite_colour = Colour()

    schema = UserSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["UserSchema"]["properties"]["favourite_colour"] == {
        "type": "string"
    }


def test_custom_field_honors_metadata_and_default():
    """Fields with `_jsonschema_type_mapping` historically lost their
    `metadata={...}` content and their `dump_default`. Regression for #21."""

    class Colour(fields.Field):
        def _jsonschema_type_mapping(self):
            return {"type": "string"}

    class TestSchema(Schema):
        favourite_colour = Colour(
            dump_default="#ffffff",
            metadata={"description": "User's favourite colour", "title": "Colour"},
        )

    dumped = validate_and_dump(TestSchema())
    prop = dumped["definitions"]["TestSchema"]["properties"]["favourite_colour"]
    assert prop == {
        "type": "string",
        "default": "#ffffff",
        "description": "User's favourite colour",
        "title": "Colour",
    }


def test_custom_field_jsonschema_type_mapping_accepts_context():
    """A custom field whose `_jsonschema_type_mapping` accepts
    `(self, json_schema, obj)` receives the JSONSchema instance and the
    schema obj, letting it call back into the dumping machinery. Used for
    wrapper-style fields that need to emit a $ref to a recursive schema.
    Regression for #165."""

    class NoOpWrapper(fields.Field):
        def __init__(self, field, **kwargs):
            self.field = field
            super().__init__(**kwargs)

        def _jsonschema_type_mapping(self, json_schema, obj):
            return json_schema._get_schema_for_field(obj, self.field)

    class ContrivedSchema(Schema):
        recursive = NoOpWrapper(fields.Nested("ContrivedSchema"))

    dumped = validate_and_dump(ContrivedSchema())
    assert dumped["definitions"]["ContrivedSchema"]["properties"]["recursive"] == {
        "type": "object",
        "$ref": "#/definitions/ContrivedSchema",
    }


def test_tuple_field():
    """`fields.Tuple` should emit a fixed-length, positionally-typed
    array. Closes #162."""

    class TestSchema(Schema):
        coords = fields.Tuple([fields.Float(), fields.Float()])
        labelled = fields.Tuple([fields.String(), fields.Integer()])

    dumped = validate_and_dump(TestSchema())
    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["coords"]["type"] == "array"
    assert props["coords"]["minItems"] == 2
    assert props["coords"]["maxItems"] == 2
    assert [item["type"] for item in props["coords"]["items"]] == ["number", "number"]
    assert [item["type"] for item in props["labelled"]["items"]] == [
        "string",
        "integer",
    ]


def test_constant_field_string():
    """`fields.Constant("hello")` should emit a `const` plus a matching
    `type`. Closes #115."""

    class TestSchema(Schema):
        api_version = fields.Constant("v2")

    dumped = validate_and_dump(TestSchema())
    prop = dumped["definitions"]["TestSchema"]["properties"]["api_version"]
    assert prop["const"] == "v2"
    assert prop["type"] == "string"


def test_constant_field_integer():
    class TestSchema(Schema):
        limit = fields.Constant(42)

    dumped = validate_and_dump(TestSchema())
    prop = dumped["definitions"]["TestSchema"]["properties"]["limit"]
    assert prop["const"] == 42
    assert prop["type"] == "integer"


def test_pluck_field_single():
    """`fields.Pluck` extracts a single field from a nested schema and
    must emit that field's schema, not a `$ref` to the whole nested
    definition."""

    class Inner(Schema):
        id = fields.Integer()
        name = fields.String()

    class Outer(Schema):
        member_id = fields.Pluck(Inner, "id")

    dumped = validate_and_dump(Outer())
    prop = dumped["definitions"]["Outer"]["properties"]["member_id"]
    assert prop["type"] == "integer"
    assert "$ref" not in prop


def test_pluck_field_many_required():
    """`Pluck(..., many=True, required=True)` wraps the picked-field
    schema in a `type: array` envelope."""

    class Inner(Schema):
        id = fields.Integer()

    class Outer(Schema):
        member_ids = fields.Pluck(Inner, "id", many=True, required=True)

    dumped = validate_and_dump(Outer())
    prop = dumped["definitions"]["Outer"]["properties"]["member_ids"]
    assert prop["type"] == "array"
    assert prop["items"]["type"] == "integer"


def test_pluck_field_many_optional_can_be_null():
    """A non-required `Pluck(many=True)` should match the same shape as
    a non-required `Nested(many=True)`: the array itself can be null."""

    class Inner(Schema):
        id = fields.Integer()

    class Outer(Schema):
        member_ids = fields.Pluck(Inner, "id", many=True)

    dumped = validate_and_dump(Outer())
    prop = dumped["definitions"]["Outer"]["properties"]["member_ids"]
    assert prop["type"] == ["array", "null"]


def test_tuple_field_honors_metadata():
    """`fields.Tuple` must honor `metadata={...}` and `dump_only` like
    other field types."""

    class TestSchema(Schema):
        coords = fields.Tuple(
            [fields.Float(), fields.Float()],
            dump_only=True,
            metadata={"title": "Coordinates", "description": "(lat, lon)"},
        )

    prop = validate_and_dump(TestSchema())["definitions"]["TestSchema"]["properties"][
        "coords"
    ]
    assert prop["title"] == "Coordinates"
    assert prop["description"] == "(lat, lon)"
    assert prop["readOnly"] is True


def test_constant_field_honors_metadata():
    """`fields.Constant` must honor `metadata={...}` and `dump_only`."""

    class TestSchema(Schema):
        api_version = fields.Constant(
            "v2",
            dump_only=True,
            metadata={"description": "Pinned API version"},
        )

    prop = validate_and_dump(TestSchema())["definitions"]["TestSchema"]["properties"][
        "api_version"
    ]
    assert prop["description"] == "Pinned API version"
    assert prop["readOnly"] is True
    assert prop["const"] == "v2"


def test_pluck_field_allow_none():
    """`Pluck(..., allow_none=True)` must wrap in anyOf [<schema>, null]
    to match `Nested`'s allow_none behavior."""

    class Inner(Schema):
        id = fields.Integer()

    class Outer(Schema):
        member_id = fields.Pluck(Inner, "id", allow_none=True)

    prop = validate_and_dump(Outer())["definitions"]["Outer"]["properties"]["member_id"]
    assert prop == {"anyOf": [{"title": "id", "type": "integer"}, {"type": "null"}]}


def test_pluck_field_outer_metadata_overrides():
    """A Pluck field's outer `metadata={...}` should win over the picked
    field's auto-derived attributes (the user is describing the OUTER
    reference, not the inner picked field)."""

    class Inner(Schema):
        id = fields.Integer()

    class Outer(Schema):
        member_id = fields.Pluck(
            Inner,
            "id",
            metadata={"title": "Member ID", "description": "A user reference"},
        )

    prop = validate_and_dump(Outer())["definitions"]["Outer"]["properties"]["member_id"]
    assert prop["title"] == "Member ID"
    assert prop["description"] == "A user reference"


def test_tuple_field_allow_none():
    class TestSchema(Schema):
        coords = fields.Tuple([fields.Float(), fields.Float()], allow_none=True)

    prop = validate_and_dump(TestSchema())["definitions"]["TestSchema"]["properties"][
        "coords"
    ]
    assert "anyOf" in prop
    assert {"type": "null"} in prop["anyOf"]


def test_constant_field_allow_none():
    class TestSchema(Schema):
        version = fields.Constant("v2", allow_none=True)

    prop = validate_and_dump(TestSchema())["definitions"]["TestSchema"]["properties"][
        "version"
    ]
    assert "anyOf" in prop
    assert {"type": "null"} in prop["anyOf"]
    assert {"const": "v2", "type": "string"} in prop["anyOf"]


def test_definitions_path_rejects_non_str():
    """`definitions_path=None` would later crash with `TypeError: argument
    of type 'NoneType' is not iterable`. Catch it at construction with a
    clear `UnsupportedValueError`."""
    with pytest.raises(UnsupportedValueError):
        JSONSchema(definitions_path=None)
    with pytest.raises(UnsupportedValueError):
        JSONSchema(definitions_path="")
    with pytest.raises(UnsupportedValueError):
        JSONSchema(definitions_path=123)


def test_field_subclass():
    """JSON schema generation should not fail on sublcass marshmallow field."""

    class CustomField(fields.Field):
        pass

    class TestSchema(Schema):
        myfield = CustomField()

    schema = TestSchema()
    with pytest.raises(UnsupportedValueError):
        _ = validate_and_dump(schema)


def test_dump_many_emits_top_level_array():
    """`Schema(many=True)` should produce a top-level array envelope
    rather than the single-object `$ref` form. Closes #92."""

    class UserSchema(Schema):
        name = fields.String()
        age = fields.Integer()

    dumped = JSONSchema().dump(UserSchema(many=True))
    assert dumped["type"] == "array"
    assert dumped["items"] == {"$ref": "#/definitions/UserSchema"}
    # The single-object `$ref` should NOT be at the root any more.
    assert "$ref" not in dumped
    # The definition itself is unchanged.
    assert "UserSchema" in dumped["definitions"]


def test_dump_single_unchanged_by_many_change():
    """Sanity: `Schema()` (single) keeps the existing root shape with
    `$ref` and no `type: array`."""

    class UserSchema(Schema):
        name = fields.String()

    dumped = JSONSchema().dump(UserSchema())
    assert dumped["$ref"] == "#/definitions/UserSchema"
    assert "type" not in dumped
    assert "items" not in dumped


@pytest.mark.skipif(
    not ALLOW_NATIVE_ENUM, reason="requires marshmallow>=3.18 for native Enum field"
)
def test_native_enum_by_value_strings():
    """`fields.Enum(MyEnum, by_value=True)` where MyEnum's values are
    strings should emit those values in the `enum` list. Closes #156."""

    class Status(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    class S(Schema):
        status = NativeEnumField(Status, by_value=True)

    prop = validate_and_dump(S())["definitions"]["S"]["properties"]["status"]
    assert sorted(prop["enum"]) == ["active", "inactive"]
    assert prop["type"] == "string"


@pytest.mark.skipif(
    not ALLOW_NATIVE_ENUM, reason="requires marshmallow>=3.18 for native Enum field"
)
def test_native_enum_by_value_non_strings_raises():
    """A by-value enum whose values aren't all strings should raise
    `NotImplementedError` with a clear pointer at the `(str, Enum)`
    workaround."""

    class NumStatus(Enum):
        ONE = 1
        TWO = 2

    class S(Schema):
        n = NativeEnumField(NumStatus, by_value=True)

    with pytest.raises(NotImplementedError) as exc:
        JSONSchema().dump(S())
    assert "str" in str(exc.value)


def test_marshmallow_enum_by_value_strings():
    """Same loosening for the third-party `marshmallow_enum.EnumField`."""

    class Status(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    class S(Schema):
        status = EnumField(Status, by_value=True)

    prop = validate_and_dump(S())["definitions"]["S"]["properties"]["status"]
    assert sorted(prop["enum"]) == ["active", "inactive"]


def test_unsupported_field_error_points_at_fix():
    """The error raised for an unmappable custom field should tell the
    user how to fix it: subclass an existing field type, or add
    `_jsonschema_type_mapping`. Regression for #157."""

    class PinCode(fields.Field):
        pass

    class TestSchema(Schema):
        pin_code = PinCode()

    with pytest.raises(UnsupportedValueError) as exc:
        JSONSchema().dump(TestSchema())

    msg = str(exc.value)
    # Names the offending field and class so users can locate it quickly.
    assert "pin_code" in msg
    assert "PinCode" in msg
    # Names both supported workarounds.
    assert "_jsonschema_type_mapping" in msg
    assert "subclass" in msg.lower()


def test_readonly():
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(dump_only=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["readonly_fld"] == {
        "title": "readonly_fld",
        "type": "string",
        "readOnly": True,
    }


def test_metadata_direct_from_field():
    """Should be able to get metadata without accessing metadata kwarg."""

    class TestSchema(Schema):
        id = fields.Integer(required=True)
        metadata_field = fields.String(
            metadata={"description": "Directly on the field!"}
        )

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["metadata_field"] == {
        "title": "metadata_field",
        "type": "string",
        "description": "Directly on the field!",
    }


def test_allow_none_on_nested():
    """A Nested field with allow_none=True should produce anyOf [$ref, null]."""

    class ChildSchema(Schema):
        id = fields.Integer(required=True)

    class TestSchema(Schema):
        id = fields.Integer(required=True)
        nested_fld = fields.Nested(ChildSchema, allow_none=True)

    schema = TestSchema()
    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["nested_fld"] == {
        "anyOf": [
            {"type": "object", "$ref": "#/definitions/ChildSchema"},
            {"type": "null"},
        ]
    }


def test_allow_none():
    """A field with allow_none set to True should have type null as additional."""

    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(allow_none=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["readonly_fld"] == {
        "title": "readonly_fld",
        "type": ["string", "null"],
    }


def test_dumps_iterable_enums():
    mapping = {"a": 0, "b": 1, "c": 2}

    class TestSchema(Schema):
        foo = fields.Integer(
            validate=validate.OneOf(mapping.values(), labels=mapping.keys())
        )

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["foo"] == {
        "enum": [v for v in mapping.values()],
        "enumNames": [k for k in mapping.keys()],
        "title": "foo",
        "type": "integer",
    }


def test_required_excluded_when_empty():
    class TestSchema(Schema):
        optional_value = fields.String()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert "required" not in dumped["definitions"]["TestSchema"]


def test_partial_true_drops_required():
    """`Schema(partial=True)` makes every field optional. The dumped
    JSON Schema should not include any of them in `required`.
    Regression for #112."""

    class TestSchema(Schema):
        name = fields.String(required=True)
        email = fields.String(required=True)

    dumped = validate_and_dump(TestSchema(partial=True))
    assert "required" not in dumped["definitions"]["TestSchema"]


def test_partial_tuple_drops_named_fields_from_required():
    """`Schema(partial=("foo",))` makes only the named fields optional.
    Other required fields should still appear in `required`.
    Regression for #112."""

    class TestSchema(Schema):
        name = fields.String(required=True)
        email = fields.String(required=True)
        age = fields.Integer(required=True)

    dumped = validate_and_dump(TestSchema(partial=("email", "age")))
    assert dumped["definitions"]["TestSchema"]["required"] == ["name"]


def test_partial_does_not_affect_non_partial_dump():
    """Sanity: with no `partial` argument the existing behavior
    (all `required=True` fields appear) must be preserved."""

    class TestSchema(Schema):
        name = fields.String(required=True)
        email = fields.String(required=True)

    dumped = validate_and_dump(TestSchema())
    assert sorted(dumped["definitions"]["TestSchema"]["required"]) == [
        "email",
        "name",
    ]


def test_required_uses_data_key():
    class TestSchema(Schema):
        optional_value = fields.String(data_key="opt", required=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    test_schema_definition = dumped["definitions"]["TestSchema"]
    assert "opt" in test_schema_definition["properties"]
    assert "optional_value" == test_schema_definition["properties"]["opt"]["title"]
    assert "required" in test_schema_definition
    assert "opt" in test_schema_definition["required"]


def test_datetime_based():
    class TestSchema(Schema):
        f_date = fields.Date()
        f_datetime = fields.DateTime()
        f_time = fields.Time()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["f_date"] == {
        "format": "date",
        "title": "f_date",
        "type": "string",
    }

    assert dumped["definitions"]["TestSchema"]["properties"]["f_datetime"] == {
        "format": "date-time",
        "title": "f_datetime",
        "type": "string",
    }

    assert dumped["definitions"]["TestSchema"]["properties"]["f_time"] == {
        "format": "time",
        "title": "f_time",
        "type": "string",
    }


def test_props_ordered_propagates_to_nested():
    """props_ordered=True on the outer JSONSchema must apply to nested
    schemas too. Regression for #109."""

    class Inner(Schema):
        z = fields.Str()
        y = fields.Str()
        x = fields.Str()

    class Outer(Schema):
        d = fields.Str()
        c = fields.Str()
        a = fields.Str()
        nested = fields.Nested(Inner)

    dumped = JSONSchema(props_ordered=True).dump(Outer())
    outer_props = list(dumped["definitions"]["Outer"]["properties"].keys())
    inner_props = list(dumped["definitions"]["Inner"]["properties"].keys())

    assert outer_props == ["d", "c", "a", "nested"]
    assert inner_props == ["z", "y", "x"]


def test_definitions_path_custom():
    """The `definitions_path` constructor argument reshapes both the root
    key holding nested definitions and the emitted $ref paths. Must be
    a single segment - multi-segment paths are rejected because they'd
    produce a flat dict key with a slash in it rather than a nested
    structure."""

    class Inner(Schema):
        foo = fields.Integer()

    class Outer(Schema):
        inner = fields.Nested(Inner)

    dumped = JSONSchema(definitions_path="schemas").dump(Outer())

    assert "definitions" not in dumped
    assert "schemas" in dumped
    assert dumped["$ref"] == "#/schemas/Outer"
    assert (
        dumped["schemas"]["Outer"]["properties"]["inner"]["$ref"] == "#/schemas/Inner"
    )


def test_definitions_path_rejects_multi_segment():
    """A multi-segment path would silently produce a flat dict key with
    slashes in it instead of the nested structure OpenAPI consumers
    expect, so we reject it at construction time."""
    with pytest.raises(UnsupportedValueError):
        JSONSchema(definitions_path="components/schemas")


def test_sorting_properties():
    # Field declaration order is preserved by marshmallow itself; what we're
    # exercising here is JSONSchema's `props_ordered` flag, which gates whether
    # the dumped properties are sorted (default) or kept in declaration order.
    class TestSchema(Schema):
        d = fields.Str()
        c = fields.Str()
        a = fields.Str()

    # Should be sorting of fields
    schema = TestSchema()

    json_schema = JSONSchema()
    data = json_schema.dump(schema)

    sorted_keys = sorted(data["definitions"]["TestSchema"]["properties"].keys())
    properties_names = [k for k in sorted_keys]
    assert properties_names == ["a", "c", "d"]

    # Should be saving ordering of fields
    schema = TestSchema()

    json_schema = JSONSchema(props_ordered=True)
    data = json_schema.dump(schema)

    keys = data["definitions"]["TestSchema"]["properties"].keys()
    properties_names = [k for k in keys]

    assert properties_names == ["d", "c", "a"]


def test_enum_based():
    class TestEnum(Enum):
        value_1 = 0
        value_2 = 1
        value_3 = 2

    class TestSchema(Schema):
        enum_prop = EnumField(TestEnum)

    # Should be sorting of fields
    schema = TestSchema()

    json_schema = JSONSchema()
    data = json_schema.dump(schema)

    assert (
        data["definitions"]["TestSchema"]["properties"]["enum_prop"]["type"] == "string"
    )
    received_enum_values = sorted(
        data["definitions"]["TestSchema"]["properties"]["enum_prop"]["enum"]
    )
    assert received_enum_values == ["value_1", "value_2", "value_3"]


def test_enum_based_load_dump_value():
    class TestEnum(Enum):
        value_1 = 0
        value_2 = 1
        value_3 = 2

    class TestSchema(Schema):
        enum_prop = EnumField(TestEnum, by_value=True)

    schema = TestSchema()

    with pytest.raises(NotImplementedError):
        validate_and_dump(schema)


def test_integer_field_emits_integer_type():
    """Regression test for #117 — Integer fields must emit `type: integer`,
    not `type: number` with a `format: integer`. Otherwise floats validate
    against integer fields."""

    class Foo(Schema):
        bar = fields.Integer()

    schema = JSONSchema().dump(Foo())
    bar_property = schema["definitions"]["Foo"]["properties"]["bar"]

    assert bar_property["type"] == "integer"
    assert "format" not in bar_property

    jsonschema.validate({"bar": 1}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"bar": 1.1}, schema)


@pytest.mark.skipif(
    not ALLOW_NATIVE_ENUM, reason="requires marshmallow>=3.18 for native Enum field"
)
def test_native_enum_based():
    class TestEnum(Enum):
        value_1 = 0
        value_2 = 1
        value_3 = 2

    class TestSchema(Schema):
        enum_prop = NativeEnumField(TestEnum)

    schema = TestSchema()

    json_schema = JSONSchema()
    data = json_schema.dump(schema)

    assert (
        data["definitions"]["TestSchema"]["properties"]["enum_prop"]["type"] == "string"
    )
    received_enum_values = sorted(
        data["definitions"]["TestSchema"]["properties"]["enum_prop"]["enum"]
    )
    assert received_enum_values == ["value_1", "value_2", "value_3"]


@pytest.mark.skipif(
    not ALLOW_NATIVE_ENUM, reason="requires marshmallow>=3.18 for native Enum field"
)
def test_native_enum_based_by_value():
    class TestEnum(Enum):
        value_1 = 0
        value_2 = 1
        value_3 = 2

    class TestSchema(Schema):
        enum_prop = NativeEnumField(TestEnum, by_value=True)

    schema = TestSchema()

    with pytest.raises(NotImplementedError):
        validate_and_dump(schema)


def test_union_based():
    class TestNestedSchema(Schema):
        field_1 = fields.String()
        field_2 = fields.Integer()

    class TestSchema(Schema):
        union_prop = Union(
            [fields.String(), fields.Integer(), fields.Nested(TestNestedSchema)]
        )

    # Should be sorting of fields
    schema = TestSchema()

    json_schema = JSONSchema()
    data = json_schema.dump(schema)

    # Expect only the `anyOf` key
    assert "anyOf" in data["definitions"]["TestSchema"]["properties"]["union_prop"]
    assert len(data["definitions"]["TestSchema"]["properties"]["union_prop"]) == 1

    string_schema = {"type": "string", "title": ""}
    integer_schema = {"type": "integer", "title": ""}
    referenced_nested_schema = {
        "type": "object",
        "$ref": "#/definitions/TestNestedSchema",
    }
    actual_nested_schema = {
        "type": "object",
        "properties": {
            "field_1": {"type": "string", "title": "field_1"},
            "field_2": {"type": "integer", "title": "field_2"},
        },
        "additionalProperties": False,
    }

    assert (
        string_schema
        in data["definitions"]["TestSchema"]["properties"]["union_prop"]["anyOf"]
    )
    assert (
        integer_schema
        in data["definitions"]["TestSchema"]["properties"]["union_prop"]["anyOf"]
    )
    assert (
        referenced_nested_schema
        in data["definitions"]["TestSchema"]["properties"]["union_prop"]["anyOf"]
    )

    assert data["definitions"]["TestNestedSchema"] == actual_nested_schema

    # Expect three possible schemas for the union type
    assert (
        len(data["definitions"]["TestSchema"]["properties"]["union_prop"]["anyOf"]) == 3
    )


def test_dumping_recursive_schema():
    """
    this reproduces issue https://github.com/fuhrysteve/marshmallow-jsonschema/issues/164
    """
    json_schema = JSONSchema()

    def generate_recursive_schema_with_name():
        class RecursiveSchema(Schema):
            # when nesting recursively you can either refer the recursive schema by its name
            nested_mwe_recursive = fields.Nested("RecursiveSchema")

        return json_schema.dump(RecursiveSchema())

    def generate_recursive_schema_with_lambda():
        class RecursiveSchema(Schema):
            # or you can use a lambda (as suggested in the marshmallow docs)
            nested_mwe_recursive = fields.Nested(lambda: RecursiveSchema())

        return json_schema.dump(
            RecursiveSchema()
        )  # this shall _not_ raise an AttributeError

    lambda_schema = generate_recursive_schema_with_lambda()
    name_schema = generate_recursive_schema_with_name()
    assert lambda_schema == name_schema
