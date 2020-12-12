from enum import Enum

import pytest
from marshmallow import Schema, fields, validate
from marshmallow_enum import EnumField
from marshmallow_union import Union

from marshmallow_jsonschema import JSONSchema, UnsupportedValueError
from . import UserSchema, validate_and_dump


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


def test_metadata():
    """Metadata should be available in the field definition."""

    class TestSchema(Schema):
        myfield = fields.String(metadata={"foo": "Bar"})
        yourfield = fields.Integer(required=True, baz="waz")

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
    assert nested_def["properties"]["foo"]["format"] == "integer"


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
    assert item_schema["type"] == "number"


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
            lambda: "string", required=True, _jsonschema_type_mapping={"type": "string"}
        )
        fn_int = fields.Function(
            lambda: 123, required=True, _jsonschema_type_mapping={"type": "number"}
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

    class UserSchema(Schema):
        favourite_colour = Invalid()

    schema = UserSchema()
    json_schema = JSONSchema()

    with pytest.raises(UnsupportedValueError):
        validate_and_dump(json_schema.dump(schema))


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


def test_field_subclass():
    """JSON schema generation should not fail on sublcass marshmallow field."""

    class CustomField(fields.Field):
        pass

    class TestSchema(Schema):
        myfield = CustomField()

    schema = TestSchema()
    with pytest.raises(UnsupportedValueError):
        _ = validate_and_dump(schema)


def test_readonly():
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(dump_only=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["readonly_fld"] == {
        "title": "readonly_fld",
        "type": "string",
        "readonly": True,
    }


def test_metadata_direct_from_field():
    """Should be able to get metadata without accessing metadata kwarg."""

    class TestSchema(Schema):
        id = fields.Integer(required=True)
        metadata_field = fields.String(description="Directly on the field!")

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["metadata_field"] == {
        "title": "metadata_field",
        "type": "string",
        "description": "Directly on the field!",
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
        "format": "integer",
        "title": "foo",
        "type": "number",
    }


def test_required_excluded_when_empty():
    class TestSchema(Schema):
        optional_value = fields.String()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert "required" not in dumped["definitions"]["TestSchema"]


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


def test_sorting_properties():
    class TestSchema(Schema):
        class Meta:
            ordered = True

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

    # Should be sorting of fields
    schema = TestSchema()

    json_schema = JSONSchema()

    with pytest.raises(NotImplementedError):
        validate_and_dump(json_schema.dump(schema))


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
    integer_schema = {"type": "string", "title": ""}
    referenced_nested_schema = {
        "type": "object",
        "$ref": "#/definitions/TestNestedSchema",
    }
    actual_nested_schema = {
        "type": "object",
        "properties": {
            "field_1": {"type": "string", "title": "field_1"},
            "field_2": {"type": "number", "title": "field_2", "format": "integer"},
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
