from marshmallow import Schema, fields, validate
from marshmallow.compat import text_type
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
    props = dumped['definitions']['UserSchema']['properties']
    for field_name, field in schema.fields.items():
        assert field_name in props

def test_default():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['UserSchema']['properties']
    assert props['id']['default'] == 'no-id'


def test_metadata():
    """Metadata should be available in the field definition."""
    class TestSchema(Schema):
        myfield = fields.String(metadata={'foo': 'Bar'})
        yourfield = fields.Integer(required=True, baz="waz")
    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['TestSchema']['properties']
    assert props['myfield']['foo'] == 'Bar'
    assert props['yourfield']['baz'] == 'waz'
    assert 'metadata' not in props['myfield']
    assert 'metadata' not in props['yourfield']

    # repeat process to assure idempotency
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['TestSchema']['properties']
    assert props['myfield']['foo'] == 'Bar'
    assert props['yourfield']['baz'] == 'waz'

def test_descriptions():
    class TestSchema(Schema):
        myfield = fields.String(metadata={'description': 'Brown Cow'})
        yourfield = fields.Integer(required=True)
    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['TestSchema']['properties']
    assert props['myfield']['description'] == 'Brown Cow'

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
    nested_def = dumped['definitions']['TestSchema']
    nested_dmp = dumped['definitions']['TestNestedSchema']['properties']['nested']
    assert nested_def['properties']['myfield']['description'] == 'Brown Cow'

    assert nested_dmp['$ref'] == '#/definitions/TestSchema'
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
    nested_def = dumped['definitions']['TestSchema']
    nested_dmp = dumped['definitions']['TestNestedSchema']['properties']['nested']
    assert nested_dmp['type'] == 'object'
    assert nested_def['properties']['foo']['format'] == 'integer'


def test_list():
    class ListSchema(Schema):
        foo = fields.List(fields.String(min), required=True)

    schema = ListSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    nested_json = dumped['definitions']['ListSchema']['properties']['foo']
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
    nested_json = dumped['definitions']['ListSchema']['properties']['bar']
    assert nested_json['type'] == 'array'
    assert 'items' in  nested_json
    item_schema = nested_json['items']
    assert 'InnerSchema' in item_schema['$ref']


def test_deep_nested():
    """Test that deep nested schemas are in definitions."""

    class InnerSchema(Schema):
        boz = fields.Integer(required=True)

    class InnerMiddleSchema(Schema):
        baz = fields.Nested(InnerSchema, required=True)

    class OuterMiddleSchema(Schema):
        bar = fields.Nested(InnerMiddleSchema, required=True)

    class OuterSchema(Schema):
        foo = fields.Nested(OuterMiddleSchema, required=True)

    schema = OuterSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    defs = dumped['definitions']
    assert 'OuterSchema' in defs
    assert 'OuterMiddleSchema' in defs
    assert 'InnerMiddleSchema' in defs
    assert 'InnerSchema' in defs


def test_respect_only_for_nested_schema():
    """Should ignore fields not in 'only' metadata for nested schemas."""
    class InnerRecursiveSchema(Schema):
        id = fields.Integer(required=True)
        baz = fields.String()
        recursive = fields.Nested('InnerRecursiveSchema')

    class MiddleSchema(Schema):
        id = fields.Integer(required=True)
        bar = fields.String()
        inner = fields.Nested('InnerRecursiveSchema', only=('id', 'baz'))

    class OuterSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested('MiddleSchema')

    schema = OuterSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    inner_props = dumped['definitions']['InnerRecursiveSchema']['properties']
    assert 'recursive' not in inner_props


def test_respect_exclude_for_nested_schema():
    """Should ignore fields in 'exclude' metadata for nested schemas."""
    class InnerRecursiveSchema(Schema):
        id = fields.Integer(required=True)
        baz = fields.String()
        recursive = fields.Nested('InnerRecursiveSchema')

    class MiddleSchema(Schema):
        id = fields.Integer(required=True)
        bar = fields.String()
        inner = fields.Nested('InnerRecursiveSchema', exclude=('recursive',))

    class OuterSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested('MiddleSchema')

    schema = OuterSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    inner_props = dumped['definitions']['InnerRecursiveSchema']['properties']
    assert 'recursive' not in inner_props


def test_respect_dotted_exclude_for_nested_schema():
    """Should ignore dotted fields in 'exclude' metadata for nested schemas."""
    class InnerRecursiveSchema(Schema):
        id = fields.Integer(required=True)
        baz = fields.String()
        recursive = fields.Nested('InnerRecursiveSchema')

    class MiddleSchema(Schema):
        id = fields.Integer(required=True)
        bar = fields.String()
        inner = fields.Nested('InnerRecursiveSchema')

    class OuterSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested('MiddleSchema', exclude=('inner.recursive',))

    schema = OuterSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    inner_props = dumped['definitions']['InnerRecursiveSchema']['properties']
    assert 'recursive' not in inner_props


def test_function():
    """Function fields can be serialised if type is given."""

    class FnSchema(Schema):
        fn_str = fields.Function(
            lambda: "string", required=True,
            _jsonschema_type_mapping={'type': 'string'}
        )
        fn_int = fields.Function(
            lambda: 123, required=True,
            _jsonschema_type_mapping={'type': 'number'}
        )

    schema = FnSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    props = dumped['definitions']['FnSchema']['properties']
    assert props['fn_int']['type'] == 'number'
    assert props['fn_str']['type'] == 'string'


def test_nested_recursive():
    """A self-referential schema should not cause an infinite recurse."""

    class RecursiveSchema(Schema):
        foo = fields.Integer(required=True)
        children = fields.Nested('RecursiveSchema', many=True)

    schema = RecursiveSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['RecursiveSchema']['properties']
    assert 'RecursiveSchema' in props['children']['items']['$ref']


def test_one_of_validator():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert (
        dumped['definitions']['UserSchema']['properties']['sex']['enum'] == [
            'male', 'female', 'non_binary', 'other'
        ]
    )
    assert (
        dumped['definitions']['UserSchema']['properties']['sex'][
            'enumNames'
        ] == [
            'Male', 'Female', 'Non-binary/fluid', 'Other'
        ]
    )


def test_range_validator():
    schema = Address()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['Address']['properties']
    assert props['floor']['minimum'] == 1
    assert props['floor']['maximum'] == 4

def test_length_validator():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    props = dumped['definitions']['UserSchema']['properties']
    assert props['name']['minLength'] == 1
    assert props['name']['maxLength'] == 255
    assert props['addresses']['minItems'] == 1
    assert props['addresses']['maxItems'] == 3
    assert props['const']['minLength'] == 50
    assert props['const']['maxLength'] == 50

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
    dumped1 = json_schema.dump(schema1).data['definitions']['SchemaMin']
    dumped2 = json_schema.dump(schema2).data['definitions']['SchemaNoMin']
    dumped1['properties']['floor']['minimum'] == 1
    dumped1['properties']['floor']['exclusiveMinimum'] is True
    dumped2['properties']['floor']['minimum'] == 0
    dumped2['properties']['floor']['exclusiveMinimum'] is False


def test_title():
    class TestSchema(Schema):
        myfield = fields.String(metadata={'title': 'Brown Cowzz'})
        yourfield = fields.Integer(required=True)
    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    _validate_schema(dumped)
    assert dumped['definitions']['TestSchema']['properties']['myfield'][
        'title'
    ] == 'Brown Cowzz'


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
    assert dumped['definitions']['UserSchema']['properties'][
        'favourite_colour'
    ] == {'type': 'string'}


def test_readonly():
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(dump_only=True)

    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    assert dumped['definitions']['TestSchema']['properties'][
        'readonly_fld'
    ] == {
        'title': 'readonly_fld',
        'type': 'string',
        'readonly': True,
    }

def test_metadata_direct_from_field():
    """Should be able to get metadata without accessing metadata kwarg."""
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        metadata_field = fields.String(description='Directly on the field!')

    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema).data
    assert dumped['definitions']['TestSchema']['properties'][
        'metadata_field'
    ] == {
        'title': 'metadata_field',
        'type': 'string',
        'description': 'Directly on the field!',
    }


def test_custom_field_by_subclassing():

    class Colour(fields.String):
        def __init__(self, default='red', **kwargs):
            super(Colour, self).__init__(default=default, **kwargs)

    class UserSchema(Schema):
        name = fields.String(required=True)
        favourite_colour = Colour()

    schema = UserSchema()
    json_schema = JSONSchema()

    with pytest.raises(ValueError):
        # The custom Color field is not registered
        dumped = json_schema.dump(schema)

    # Provide the custom field to the default mappings
    class CustomJSONSchema(JSONSchema):
        def get_custom_mappings(self):
            return {Colour:  text_type}

    # Register the field
    json_schema = CustomJSONSchema()
    dumped = json_schema.dump(schema).data
    assert dumped['definitions']['UserSchema']['properties']['favourite_colour'] == {
        'default': 'red',
        'title': 'favourite_colour',
        'type': 'string'}


def test_nested_custom_field_by_subclassing():

    class Colour(fields.String):
        def __init__(self, default='red', **kwargs):
            super(Colour, self).__init__(default=default, **kwargs)

    class ColoursSchema(Schema):
        favourite_colour = Colour()

    class UserSchema(Schema):
        name = fields.String(required=True)
        colours = fields.Nested(ColoursSchema)

    schema = UserSchema()
    json_schema = JSONSchema()

    with pytest.raises(ValueError):
        # The custom Color field is not registered
        dumped = json_schema.dump(schema)

    # Provide the custom field to the default mappings
    class CustomJSONSchema(JSONSchema):
        def get_custom_mappings(self):
            return {Colour:  text_type}

    # Register the field
    json_schema = CustomJSONSchema()
    dumped = json_schema.dump(schema).data
    assert dumped['definitions']['ColoursSchema']['properties']['favourite_colour'] == {
        'default': 'red',
        'title': 'favourite_colour',
        'type': 'string'}
