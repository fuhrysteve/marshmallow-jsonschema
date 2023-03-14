import pytest
from marshmallow import Schema, fields, RAISE, INCLUDE, EXCLUDE

from marshmallow_jsonschema import UnsupportedValueError, JSONSchema
from . import validate_and_dump


def test_additional_properties_default():
    class TestSchema(Schema):
        foo = fields.Integer()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert not dumped["definitions"]["TestSchema"]["additionalProperties"]


@pytest.mark.parametrize("additional_properties_value", (False, True))
def test_additional_properties_from_meta(additional_properties_value):
    class TestSchema(Schema):
        class Meta:
            additional_properties = additional_properties_value

        foo = fields.Integer()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert (
        dumped["definitions"]["TestSchema"]["additionalProperties"]
        == additional_properties_value
    )


def test_additional_properties_invalid_value():
    class TestSchema(Schema):
        class Meta:
            additional_properties = "foo"

        foo = fields.Integer()

    schema = TestSchema()
    json_schema = JSONSchema()

    with pytest.raises(UnsupportedValueError):
        json_schema.dump(schema)


def test_additional_properties_nested_default():
    class TestNestedSchema(Schema):
        foo = fields.Integer()

    class TestSchema(Schema):
        nested = fields.Nested(TestNestedSchema())

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert not dumped["definitions"]["TestSchema"]["additionalProperties"]


@pytest.mark.parametrize("additional_properties_value", (False, True))
def test_additional_properties_from_nested_meta(additional_properties_value):
    class TestNestedSchema(Schema):
        class Meta:
            additional_properties = additional_properties_value

        foo = fields.Integer()

    class TestSchema(Schema):
        nested = fields.Nested(TestNestedSchema())

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert (
        dumped["definitions"]["TestNestedSchema"]["additionalProperties"]
        == additional_properties_value
    )


@pytest.mark.parametrize(
    "unknown_value, additional_properties",
    ((RAISE, False), (INCLUDE, True), (EXCLUDE, False)),
)
def test_additional_properties_deduced(unknown_value, additional_properties):
    class TestSchema(Schema):
        class Meta:
            unknown = unknown_value

        foo = fields.Integer()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert (
        dumped["definitions"]["TestSchema"]["additionalProperties"]
        == additional_properties
    )
