from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema
from jsonschema import Draft4Validator

from . import BaseTest, UserSchema, Address


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

    def test_descriptions(self):
        class TestSchema(Schema):
            myfield = fields.String(metadata={'description': 'Brown Cow'})
            yourfield = fields.Integer(required=True)
        schema = TestSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        assert dumped['properties']['myfield']['description'] == 'Brown Cow'

    def test_one_of_validator(self):
        schema = UserSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        self.assertEqual(dumped['properties']['sex']['enum'],
                         ['male', 'female'])

    def test_range_validator(self):
        schema = Address()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        self.assertEqual(dumped['properties']['floor']['minimum'], 1)
        self.assertEqual(dumped['properties']['floor']['maximum'], 4)

    def test_length_validator(self):
        schema = UserSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        self.assertEqual(dumped['properties']['name']['minLength'], 1)
        self.assertEqual(dumped['properties']['name']['maxLength'], 255)
        self.assertEqual(dumped['properties']['addresses']['minItems'], 1)
        self.assertEqual(dumped['properties']['addresses']['maxItems'], 3)
        self.assertEqual(dumped['properties']['const']['minLength'], 50)
        self.assertEqual(dumped['properties']['const']['maxLength'], 50)

    def test_title(self):
        class TestSchema(Schema):
            myfield = fields.String(metadata={'title': 'Brown Cowzz'})
            yourfield = fields.Integer(required=True)
        schema = TestSchema()
        json_schema = JSONSchema()
        dumped = json_schema.dump(schema).data
        self._validate_schema(dumped)
        self.assertEqual(dumped['properties']['myfield']['title'],
                         'Brown Cowzz')

    def test_unknown_typed_field_throws_valueerror(self):

        class Invalid(fields.Field):
            def _serialize(self, value, attr, obj):
                return value

        class UserSchema(Schema):
            favourite_colour = Invalid()

        schema = UserSchema()
        json_schema = JSONSchema()
        with self.assertRaises(ValueError):
            json_schema.dump(schema).data

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
