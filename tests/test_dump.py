import json

import marshmallow
from marshmallow import Schema, fields, validate
from marshmallow_jsonschema import JSONSchema
from jsonschema import Draft4Validator
import pytest

from . import UserSchema, Address

# marshmallow v3 doesn't do the .data thing
if marshmallow.__version__.split('.', 1)[0] >= '3':
    def compat_data(dumped):
        return dumped
else:
    def compat_data(dumped):
        return dumped.data


def _validate_schema(schema):
    '''
    raises jsonschema.exceptions.SchemaError
    '''
    Draft4Validator.check_schema(schema)


def test_dump_schema():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
    _validate_schema(dumped)
    assert len(schema.fields) > 1
    props = dumped['definitions']['UserSchema']['properties']
    for field_name, field in schema.fields.items():
        assert field_name in props


def test_default():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
    _validate_schema(dumped)
    props = dumped['definitions']['TestSchema']['properties']
    assert props['myfield']['foo'] == 'Bar'
    assert props['yourfield']['baz'] == 'waz'
    assert 'metadata' not in props['myfield']
    assert 'metadata' not in props['yourfield']

    # repeat process to assure idempotency
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
    _validate_schema(dumped)
    nested_json = dumped['definitions']['ListSchema']['properties']['foo']
    assert nested_json['type'] == 'array'
    assert 'items' in nested_json
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
    dumped = compat_data(json_schema.dump(schema))
    _validate_schema(dumped)
    nested_json = dumped['definitions']['ListSchema']['properties']['bar']
    assert nested_json['type'] == 'array'
    assert 'items' in nested_json
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
    _validate_schema(dumped)
    props = dumped['definitions']['RecursiveSchema']['properties']
    assert 'RecursiveSchema' in props['children']['items']['$ref']


def test_one_of_validator():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
    _validate_schema(dumped)
    props = dumped['definitions']['Address']['properties']
    assert props['floor']['minimum'] == 1
    assert props['floor']['maximum'] == 4


def test_length_validator():
    schema = UserSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
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
        class Meta:
            strict = True

    schema = BadSchema()
    json_schema = JSONSchema()
    with pytest.raises(ValueError):
        json_schema.dump(schema)


def test_handle_range_not_number_returns_same_instance():
    class SchemaWithStringRange(Schema):
        floor = fields.String(validate=validate.Range(min=1, max=4))
        class Meta:
            strict = True

    class SchemaWithNoRange(Schema):
        floor = fields.String()
        class Meta:
            strict = True

    class SchemaWithIntRangeValidate(Schema):
        floor = fields.Integer(validate=validate.Range(min=1, max=4))
        class Meta:
            strict = True

    class SchemaWithIntRangeNoValidate(Schema):
        floor = fields.Integer()
        class Meta:
            strict = True

    schema1 = SchemaWithStringRange()
    schema2 = SchemaWithNoRange()
    schema3 = SchemaWithIntRangeValidate()
    schema4 = SchemaWithIntRangeNoValidate()
    json_schema = JSONSchema()
    json_schema.dump(schema1) == json_schema.dump(schema2)
    json_schema.dump(schema3) != json_schema.dump(schema4)


def test_handle_range_no_minimum():
    class SchemaMin(Schema):
        floor = fields.Integer(validate=validate.Range(min=1, max=4))
        class Meta:
            strict = True

    class SchemaNoMin(Schema):
        floor = fields.Integer(validate=validate.Range(max=4))
        class Meta:
            strict = True

    schema1 = SchemaMin()
    schema2 = SchemaNoMin()
    json_schema = JSONSchema()
    dumped1 = compat_data(json_schema.dump(schema1))['definitions']['SchemaMin']
    dumped2 = compat_data(json_schema.dump(schema2))['definitions']['SchemaNoMin']
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
    dumped = compat_data(json_schema.dump(schema))
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
        compat_data(json_schema.dump(schema))


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
    dumped = compat_data(json_schema.dump(schema))
    assert dumped['definitions']['UserSchema']['properties'][
               'favourite_colour'
           ] == {'type': 'string'}


def test_readonly():
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(dump_only=True)

    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
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
    dumped = compat_data(json_schema.dump(schema))
    assert dumped['definitions']['TestSchema']['properties'][
               'metadata_field'
           ] == {
               'title': 'metadata_field',
               'type': 'string',
               'description': 'Directly on the field!',
           }


def test_dumps_iterable_enums():
    mapping = {'a': 0, 'b': 1, 'c': 2}

    class TestSchema(Schema):
        foo = fields.Integer(validate=validate.OneOf(
            mapping.values(), labels=mapping.keys()))

    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))

    assert dumped['definitions']['TestSchema']['properties']['foo'] == {
        'enum': [v for v in mapping.values()],
        'enumNames': [k for k in mapping.keys()],
        'format': 'integer',
        'title': 'foo',
        'type': 'number'
    }


def test_required_excluded_when_empty():
    class TestSchema(Schema):
        optional_value = fields.String()

    schema = TestSchema()
    json_schema = JSONSchema()
    dumped = compat_data(json_schema.dump(schema))
    assert 'required' not in dumped['definitions']['TestSchema']


def test_use_datakey_for_title():
    # use datakey for marshmallow v3
    if marshmallow.__version__.split('.', 1)[0] >= '3':
        class TestSchema(Schema):
            normal_field = fields.String()
            data_key = fields.String(data_key='dataKey')
            required = fields.String(data_key='isRequired', required = True)

        schema = TestSchema()
        json_schema = JSONSchema(prefer_data_key=True)
        dumped = compat_data(json_schema.dump(schema))

        normal_field = dumped['definitions']['TestSchema']['properties'].get('normal_field')
        assert normal_field is not None
        assert normal_field.get('title') == 'normal_field'

        data_key = dumped['definitions']['TestSchema']['properties'].get('dataKey')
        assert data_key is not None
        assert data_key.get('title') == 'dataKey'

        required = dumped['definitions']['TestSchema']['required']
        assert 'isRequired' in required

    # use load_from, then dump_to for marshmallow < v3
    else:
        class TestSchema(Schema):
            normal_field = fields.String()
            load_from = fields.String(load_from='loadFrom')
            dump_to = fields.String(dump_to='dumpTo')
            prefer_load_from = fields.String(load_from='both', dump_to='dumpTo')
            required = fields.String(dump_to='isRequired', required=True)

        schema = TestSchema()
        json_schema = JSONSchema(prefer_data_key=True)
        dumped = compat_data(json_schema.dump(schema))

        normal_field = dumped['definitions']['TestSchema']['properties'].get('normal_field')
        assert normal_field is not None
        assert normal_field.get('title') == 'normal_field'

        load_from = dumped['definitions']['TestSchema']['properties'].get('loadFrom')
        print(json.dumps(dumped, indent=4))
        assert load_from is not None
        assert load_from.get('title') == 'loadFrom'

        dump_to = dumped['definitions']['TestSchema']['properties'].get('dumpTo')
        assert dump_to is not None
        assert dump_to.get('title') == 'dumpTo'

        prefer_load_from = dumped['definitions']['TestSchema']['properties'].get('both')
        assert prefer_load_from is not None
        assert prefer_load_from.get('title') == 'both'

        required = dumped['definitions']['TestSchema']['required']
        assert 'isRequired' in required
