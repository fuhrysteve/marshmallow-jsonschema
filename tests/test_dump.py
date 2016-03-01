from marshmallow_jsonschema import JSONSchema
from jsonschema import Draft4Validator

from . import BaseTest, UserSchema


class TestDumpSchema(BaseTest):

    def _validate_schema(self, schema):
        '''
        raises jsonschema.exceptions.SchemaError
        '''
        Draft4Validator.check_schema(schema)

    def test_dump_schema(self):
        schema = UserSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        self.assertGreater(len(schema.fields), 1)
        for field_name, field in schema.fields.items():
            self.assertIn(field_name, dumped['properties'])

    def test_default(self):
        schema = UserSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        self.assertEqual(dumped['properties']['id']['default'], 'no-id')
