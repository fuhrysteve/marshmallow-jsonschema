import pytest
from marshmallow import Schema, fields

from marshmallow_jsonschema import UnsupportedValueError, JSONSchema
from .. import validate_and_dump


class TestDescriptionSchemaMetadata:

    def test_title_default(self):
        class TestSchema(Schema):
            foo = fields.Integer()

        schema = TestSchema()
        dumped = validate_and_dump(schema)
        definition_to_test = dumped["definitions"]["TestSchema"]
        assert "title" not in definition_to_test

    @pytest.mark.parametrize("title_value", ("desc1", "desc2"))
    def test_title_from_meta(self, title_value):
        class TestSchema(Schema):
            class Meta:
                title = title_value
            foo = fields.Integer()

        schema = TestSchema()
        dumped = validate_and_dump(schema)

        assert (
            dumped["definitions"]["TestSchema"]["title"]
            == title_value
        )

    @pytest.mark.parametrize("invalid_value", [
        True,
        4,
        {}
    ])
    def test_title_invalid_value(self, invalid_value):
        class TestSchema(Schema):
            class Meta:
                title = invalid_value
            foo = fields.Integer()

        schema = TestSchema()
        json_schema = JSONSchema()

        with pytest.raises(UnsupportedValueError):
            json_schema.dump(schema)


class TestDescriptionNestedSchemaMetadata:

    def test_title_default(self):
        class TestNestedSchema(Schema):
            foo = fields.Integer()

        class TestSchema(Schema):
            nested = fields.Nested(TestNestedSchema())

        schema = TestSchema()
        dumped = validate_and_dump(schema)
        definition_to_test = dumped["definitions"]["TestNestedSchema"]
        assert "title" not in definition_to_test

    @pytest.mark.parametrize("title_value", ("desc1", "desc2"))
    def test_title_from_meta(self, title_value):
        class TestNestedSchema(Schema):
            class Meta:
                title = title_value
            foo = fields.Integer()

        class TestSchema(Schema):
            nested = fields.Nested(TestNestedSchema())

        schema = TestSchema()
        dumped = validate_and_dump(schema)

        assert (
            dumped["definitions"]["TestNestedSchema"]["title"]
            == title_value
        )

    @pytest.mark.parametrize("invalid_value", [
        True,
        4,
        {}
    ])
    def test_title_invalid_value(self, invalid_value):
        class TestNestedSchema(Schema):
            class Meta:
                title = invalid_value
            foo = fields.Integer()

        class TestSchema(Schema):
            nested = fields.Nested(TestNestedSchema())

        schema = TestSchema()
        json_schema = JSONSchema()

        with pytest.raises(UnsupportedValueError):
            json_schema.dump(schema)
