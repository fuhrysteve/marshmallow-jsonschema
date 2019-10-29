import pytest
from marshmallow import Schema, fields

from marshmallow_jsonschema import JSONSchema
from .. import validate_and_dump


@pytest.mark.parametrize("unchecked_value", (False, True))
def test_unhandled_metas_do_not_pollute_schema(unchecked_value):

    class TestSchema(Schema):
        class Meta:
            unhandled = unchecked_value

        foo = fields.Integer()

    schema = TestSchema()
    dumped = validate_and_dump(schema)

    definition_to_check = dumped["definitions"]["TestSchema"]

    assert "unhandled" not in definition_to_check
