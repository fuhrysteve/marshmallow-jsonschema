import pytest
from marshmallow import Schema, fields, validate

from marshmallow_jsonschema import JSONSchema
from . import UserSchema, Address, validate_and_dump


def test_one_of_validator():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["UserSchema"]["properties"]["sex"]["enum"] == [
        "male",
        "female",
        "non_binary",
        "other",
    ]
    assert dumped["definitions"]["UserSchema"]["properties"]["sex"]["enumNames"] == [
        "Male",
        "Female",
        "Non-binary/fluid",
        "Other",
    ]


def test_range_validator():
    schema = Address()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["Address"]["properties"]
    assert props["floor"]["minimum"] == 1
    assert props["floor"]["maximum"] == 4


def test_length_validator():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["UserSchema"]["properties"]
    assert props["name"]["minLength"] == 1
    assert props["name"]["maxLength"] == 255
    assert props["addresses"]["minItems"] == 1
    assert props["addresses"]["maxItems"] == 3
    assert props["const"]["minLength"] == 50
    assert props["const"]["maxLength"] == 50


def test_length_validator_value_error():
    class BadSchema(Schema):
        bob = fields.Integer(validate=validate.Length(min=1, max=3))

        class Meta:
            strict = True

    schema = BadSchema()
    json_schema = JSONSchema()

    with pytest.raises(ValueError):
        json_schema.dump(schema)


def test_handle_range_no_minimum():
    class SchemaMin(Schema):
        floor = fields.Integer(validate=validate.Range(min=1, max=4))

        class Meta:
            strict = True

    class SchemaNoMin(Schema):
        floor = fields.Integer(validate=validate.Range(max=4))

        class Meta:
            strict = True

    schema1 = SchemaMin()
    schema2 = SchemaNoMin()

    dumped1 = validate_and_dump(schema1)["definitions"]["SchemaMin"]
    dumped2 = validate_and_dump(schema2)["definitions"]["SchemaNoMin"]
    assert dumped1["properties"]["floor"]["minimum"] == 1
    assert "exclusiveMinimum" not in dumped1["properties"]["floor"].keys()
    assert "minimum" not in dumped2["properties"]["floor"]
    assert "exclusiveMinimum" not in dumped2["properties"]["floor"]
