import pytest
from marshmallow import Schema, fields, validate

from marshmallow_jsonschema import JSONSchema
from marshmallow_jsonschema.compat import dot_data_backwards_compatible
from . import UserSchema, Address, _validate_schema


def test_one_of_validator():
    schema = UserSchema()
    json_schema = JSONSchema()

    dumped = dot_data_backwards_compatible(json_schema.dump(schema))

    _validate_schema(dumped)

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
    json_schema = JSONSchema()

    dumped = dot_data_backwards_compatible(json_schema.dump(schema))

    _validate_schema(dumped)

    props = dumped["definitions"]["Address"]["properties"]
    assert props["floor"]["minimum"] == 1
    assert props["floor"]["maximum"] == 4


def test_length_validator():
    schema = UserSchema()
    json_schema = JSONSchema()

    dumped = dot_data_backwards_compatible(json_schema.dump(schema))

    _validate_schema(dumped)

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


def test_handle_range_not_number_returns_same_instance():
    class SchemaWithStringRange(Schema):
        floor = fields.String(validate=validate.Range(min=1, max=4))

        class Meta:
            strict = True

    class SchemaWithNoRange(Schema):
        floor = fields.String()

        class Meta:
            strict = True

    class SchemaWithIntRangeValidate(Schema):
        floor = fields.Integer(validate=validate.Range(min=1, max=4))

        class Meta:
            strict = True

    class SchemaWithIntRangeNoValidate(Schema):
        floor = fields.Integer()

        class Meta:
            strict = True

    schema1 = SchemaWithStringRange()
    schema2 = SchemaWithNoRange()
    schema3 = SchemaWithIntRangeValidate()
    schema4 = SchemaWithIntRangeNoValidate()
    json_schema = JSONSchema()

    # Delete "$ref" as root object names will obviously differ for schemas with different names
    dumped_1 = dot_data_backwards_compatible(json_schema.dump(schema1))
    del dumped_1["$ref"]
    dumped_2 = dot_data_backwards_compatible(json_schema.dump(schema2))
    del dumped_2["$ref"]

    assert dumped_1 == dumped_2
    assert json_schema.dump(schema3) != json_schema.dump(schema4)


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
    json_schema = JSONSchema()

    dumped1 = dot_data_backwards_compatible(json_schema.dump(schema1))["definitions"][
        "SchemaMin"
    ]
    dumped2 = dot_data_backwards_compatible(json_schema.dump(schema2))["definitions"][
        "SchemaNoMin"
    ]
    assert dumped1["properties"]["floor"]["minimum"] == 1
    assert "exclusiveMinimum" not in dumped1["properties"]["floor"].keys()
    assert "minimum" not in dumped2["properties"]["floor"]
    assert "exclusiveMinimum" not in dumped2["properties"]["floor"]
