from marshmallow import Schema, fields
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

    def test_unknown_typed_field_throws_valueerror(self):

        class Invalid(fields.Field):
            def _serialize(self, value, attr, obj):
                return value

        class UserSchema(Schema):
            favourite_colour = Invalid()

        schema = UserSchema()
        json_schema = JSONSchema()
        with self.assertRaises(ValueError):
            dumped = json_schema.dump(schema).data

    def test_unknown_typed_field(self):

        class Colour(fields.Field):

            def _jsonschema_type_mapping(self):
                return {
                    'type': 'string',
                }

            def _serialize(self, value, attr, obj):
                r, g, b = value
                r = hex(r)[2:]
                g = hex(g)[2:]
                b = hex(b)[2:]
                return '#' + r + g + b

        class UserSchema(Schema):
            name = fields.String(required=True)
            favourite_colour = Colour()

        schema = UserSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self.assertEqual(dumped['properties']['favourite_colour'],
                         {'type': 'string'})

    def test_property_order(self):

        class UserSchema(Schema):
            first = fields.String()
            second = fields.String()
            third = fields.String()
            fourth = fields.String()

            class Meta:
                ordered = True

        schema = UserSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self.assertEqual(dumped['properties']['first']['propertyOrder'], 1)
        self.assertEqual(dumped['properties']['second']['propertyOrder'], 2)
        self.assertEqual(dumped['properties']['third']['propertyOrder'], 3)
        self.assertEqual(dumped['properties']['fourth']['propertyOrder'], 4)
