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


def test_schema_level_title_propagates():
    class TestSchema(Schema):
        class Meta:
            title = "My Nice Title"

        foo = fields.Integer()

    dumped = validate_and_dump(TestSchema())
    assert dumped["definitions"]["TestSchema"]["title"] == "My Nice Title"


def test_schema_level_description_propagates():
    class TestSchema(Schema):
        class Meta:
            description = "My lengthy description."

        foo = fields.Integer()

    dumped = validate_and_dump(TestSchema())
    assert (
        dumped["definitions"]["TestSchema"]["description"] == "My lengthy description."
    )


def test_schema_level_meta_string_on_nested():
    class TestNestedSchema(Schema):
        class Meta:
            title = "Inner Title"
            description = "Inner description."

        foo = fields.Integer()

    class TestSchema(Schema):
        nested = fields.Nested(TestNestedSchema())

    dumped = validate_and_dump(TestSchema())
    nested_def = dumped["definitions"]["TestNestedSchema"]
    assert nested_def["title"] == "Inner Title"
    assert nested_def["description"] == "Inner description."


@pytest.mark.parametrize("meta_key", ("title", "description"))
def test_schema_level_meta_string_rejects_non_str(meta_key):
    class TestSchema(Schema):
        foo = fields.Integer()

    setattr(TestSchema.Meta, meta_key, 123)
    try:
        with pytest.raises(UnsupportedValueError):
            JSONSchema().dump(TestSchema())
    finally:
        delattr(TestSchema.Meta, meta_key)


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
