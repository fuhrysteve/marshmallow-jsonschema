import pytest
from marshmallow import Schema, fields

from marshmallow_jsonschema import UnsupportedValueError, JSONSchema
from .. import validate_and_dump


class TestDescriptionSchemaMetadata:

    def test_description_default(self):
        class TestSchema(Schema):
            foo = fields.Integer()

        schema = TestSchema()
        dumped = validate_and_dump(schema)
        definition_to_test = dumped["definitions"]["TestSchema"]
        assert "description" not in definition_to_test

    @pytest.mark.parametrize("description_value", ("desc1", "desc2"))
    def test_description_from_meta(self, description_value):
        class TestSchema(Schema):
            class Meta:
                description = description_value
            foo = fields.Integer()

        schema = TestSchema()
        dumped = validate_and_dump(schema)

        assert (
            dumped["definitions"]["TestSchema"]["description"]
            == description_value
        )

    @pytest.mark.parametrize("invalid_value", [
        True,
        4,
        {}
    ])
    def test_description_invalid_value(self, invalid_value):
        class TestSchema(Schema):
            class Meta:
                description = invalid_value
            foo = fields.Integer()

        schema = TestSchema()
        json_schema = JSONSchema()

        with pytest.raises(UnsupportedValueError):
            json_schema.dump(schema)


class TestDescriptionNestedSchemaMetadata:

    def test_description_default(self):
        class TestNestedSchema(Schema):
            foo = fields.Integer()

        class TestSchema(Schema):
            nested = fields.Nested(TestNestedSchema())

        schema = TestSchema()
        dumped = validate_and_dump(schema)
        definition_to_test = dumped["definitions"]["TestNestedSchema"]
        assert "description" not in definition_to_test

    @pytest.mark.parametrize("description_value", ("desc1", "desc2"))
    def test_description_from_meta(self, description_value):
        class TestNestedSchema(Schema):
            class Meta:
                description = description_value
            foo = fields.Integer()

        class TestSchema(Schema):
            nested = fields.Nested(TestNestedSchema())

        schema = TestSchema()
        dumped = validate_and_dump(schema)

        assert (
            dumped["definitions"]["TestNestedSchema"]["description"]
            == description_value
        )

    @pytest.mark.parametrize("invalid_value", [
        True,
        4,
        {}
    ])
    def test_description_invalid_value(self, invalid_value):
        class TestNestedSchema(Schema):
            class Meta:
                description = invalid_value
            foo = fields.Integer()

        class TestSchema(Schema):
            nested = fields.Nested(TestNestedSchema())

        schema = TestSchema()
        json_schema = JSONSchema()

        with pytest.raises(UnsupportedValueError):
            json_schema.dump(schema)
