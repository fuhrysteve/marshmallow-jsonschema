from marshmallow import Schema, fields, validate
from marshmallow_jsonschema import JSONSchema
from jsonschema import Draft4Validator
import pytest

from . import BaseTest, UserSchema, Address


def _validate_schema(schema):
    '''
    raises jsonschema.exceptions.SchemaError
    '''
    Draft4Validator.check_schema(schema)

def test_dump_schema():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert len(schema.fields) > 1
    for field_name, field in schema.fields.items():
        assert field_name in dumped['properties']

def test_default():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['properties']['id']['default'] == 'no-id'

def test_descriptions():
    class TestSchema(Schema):
        myfield = fields.String(metadata={'description': 'Brown Cow'})
        yourfield = fields.Integer(required=True)
    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['properties']['myfield']['description'] == 'Brown Cow'

def test_nested_descriptions():
    class TestSchema(Schema):
        myfield = fields.String(metadata={'description': 'Brown Cow'})
        yourfield = fields.Integer(required=True)
    class TestNestedSchema(Schema):
        nested = fields.Nested(
            TestSchema, metadata={'description': 'Nested 1', 'title': 'Title1'})
        yourfield_nested = fields.Integer(required=True)

    schema = TestNestedSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    nested_dmp = dumped['properties']['nested']
    assert nested_dmp['properties']['myfield']['description'] == 'Brown Cow'
    assert nested_dmp['description'] == 'Nested 1'
    assert nested_dmp['title'] == 'Title1'


def test_nested_string_to_cls():
    class TestSchema(Schema):
        foo = fields.Integer(required=True)

    class TestNestedSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested('TestSchema')
    schema = TestNestedSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    nested_json = dumped['properties']['nested']
    assert nested_json['properties']['foo']['format'] == 'integer'
    assert nested_json['type'] == 'object'


def test_list():
    class ListSchema(Schema):
        foo = fields.List(fields.String(min), required=True)

    schema = ListSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    nested_json = dumped['properties']['foo']
    assert nested_json['type'] == 'array'
    assert 'items' in  nested_json
    item_schema = nested_json['items']
    assert item_schema['type'] == 'string'


def test_list_nested():
    """Test that a list field will work with an inner nested field."""

    class InnerSchema(Schema):
        foo = fields.Integer(required=True)

    class ListSchema(Schema):
        bar = fields.List(fields.Nested(InnerSchema), required=True)

    schema = ListSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    nested_json = dumped['properties']['bar']
    assert nested_json['type'] == 'array'
    assert 'items' in  nested_json
    item_schema = nested_json['items']
    assert 'foo' in item_schema['properties']


def test_one_of_validator():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['properties']['sex']['enum'] == ['male', 'female']


def test_range_validator():
    schema = Address()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['properties']['floor']['minimum'] == 1
    assert dumped['properties']['floor']['maximum'] == 4

def test_length_validator():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['properties']['name']['minLength'] == 1
    assert dumped['properties']['name']['maxLength'] == 255
    assert dumped['properties']['addresses']['minItems'] == 1
    assert dumped['properties']['addresses']['maxItems'] == 3
    assert dumped['properties']['const']['minLength'] == 50
    assert dumped['properties']['const']['maxLength'] == 50

def test_length_validator_value_error():
    class BadSchema(Schema):
        bob = fields.Integer(validate=validate.Length(min=1, max=3))
    schema = BadSchema(strict=True)
    json_schema = JSONSchema()
    with pytest.raises(ValueError):
        json_schema.dump(schema)


def test_handle_range_not_number_returns_same_instance():
    class SchemaWithStringRange(Schema):
        floor = fields.String(validate=validate.Range(min=1, max=4))
    class SchemaWithNoRange(Schema):
        floor = fields.String()
    class SchemaWithIntRangeValidate(Schema):
        floor = fields.Integer(validate=validate.Range(min=1, max=4))
    class SchemaWithIntRangeNoValidate(Schema):
        floor = fields.Integer()
    schema1 = SchemaWithStringRange(strict=True)
    schema2 = SchemaWithNoRange(strict=True)
    schema3 = SchemaWithIntRangeValidate(strict=True)
    schema4 = SchemaWithIntRangeNoValidate(strict=True)
    json_schema = JSONSchema()
    json_schema.dump(schema1) == json_schema.dump(schema2)
    json_schema.dump(schema3) != json_schema.dump(schema4)


def test_handle_range_no_minimum():
    class SchemaMin(Schema):
        floor = fields.Integer(validate=validate.Range(min=1, max=4))
    class SchemaNoMin(Schema):
        floor = fields.Integer(validate=validate.Range(max=4))
    schema1 = SchemaMin(strict=True)
    schema2 = SchemaNoMin(strict=True)
    json_schema = JSONSchema()
    dumped1 = json_schema.dump(schema1)
    dumped2 = json_schema.dump(schema2)
    dumped1.data['properties']['floor']['minimum'] == 1
    dumped1.data['properties']['floor']['exclusiveMinimum'] is True
    dumped2.data['properties']['floor']['minimum'] == 0
    dumped2.data['properties']['floor']['exclusiveMinimum'] is False


def test_title():
    class TestSchema(Schema):
        myfield = fields.String(metadata={'title': 'Brown Cowzz'})
        yourfield = fields.Integer(required=True)
    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['properties']['myfield']['title'] == 'Brown Cowzz'

def test_unknown_typed_field_throws_valueerror():

    class Invalid(fields.Field):
        def _serialize(self, value, attr, obj):
            return value

    class UserSchema(Schema):
        favourite_colour = Invalid()

    schema = UserSchema()
    json_schema = JSONSchema()
    with pytest.raises(ValueError):
        json_schema.dump(schema).data

def test_unknown_typed_field():

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
    assert dumped['properties']['favourite_colour'] == {'type': 'string'}


def test_readonly():
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(dump_only=True)

    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    assert dumped['properties']['readonly_fld'] == {
        'title': 'readonly_fld',
        'type': 'string',
        'readonly': True,
    }
