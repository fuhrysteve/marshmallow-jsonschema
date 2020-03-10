import pytest
from marshmallow import Schema, fields, validate
from marshmallow.validate import OneOf, Range

from marshmallow_jsonschema import JSONSchema, UnsupportedValueError
from marshmallow_jsonschema.compat import MARSHMALLOW_2, MARSHMALLOW_3
from . import UserSchema, validate_and_dump


def test_length_validator():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["UserSchema"]["properties"]
    assert props["name"]["minLength"] == 1
    assert props["name"]["maxLength"] == 255
    assert props["addresses"]["minItems"] == 1
    assert props["addresses"]["maxItems"] == 3
    assert props["const"]["minLength"] == 50
    assert props["const"]["maxLength"] == 50


def test_length_validator_error():
    class BadSchema(Schema):
        bob = fields.Integer(validate=validate.Length(min=1, max=3))

        class Meta:
            strict = True

    schema = BadSchema()
    json_schema = JSONSchema()

    with pytest.raises(UnsupportedValueError):
        json_schema.dump(schema)


def test_one_of_validator():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["UserSchema"]["properties"]["sex"]["enum"] == [
        "male",
        "female",
        "non_binary",
        "other",
    ]
    assert dumped["definitions"]["UserSchema"]["properties"]["sex"]["enumNames"] == [
        "Male",
        "Female",
        "Non-binary/fluid",
        "Other",
    ]


def test_one_of_empty_enum():
    class TestSchema(Schema):
        foo = fields.String(validate=OneOf([]))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    foo_property = dumped["definitions"]["TestSchema"]["properties"]["foo"]
    assert foo_property["enum"] == []
    assert foo_property["enumNames"] == []


@pytest.mark.skipif(MARSHMALLOW_3, reason="marshmallow 2 only")
def test_range_marshmallow_2():
    class TestSchema(Schema):
        foo = fields.Integer(validate=Range(min=1, max=3))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["foo"]["minimum"] == 1
    assert props["foo"]["maximum"] == 3


@pytest.mark.skipif(MARSHMALLOW_3, reason="fixed in marshmallow 3")
def test_doubly_nested_skipped_titles():
    class TestSchema(Schema):
        foo = fields.List(fields.List(fields.Integer()))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]

    assert props["foo"]["title"] == "foo"
    assert props["foo"]["items"]["title"] == "foo"
    with pytest.raises(KeyError):
        props["foo"]["items"]["items"]["title"]


@pytest.mark.skipif(MARSHMALLOW_2, reason="marshmallow 3 only")
def test_range_marshmallow_3():
    class TestSchema(Schema):
        foo = fields.Integer(
            validate=Range(min=1, min_inclusive=False, max=3, max_inclusive=False)
        )
        bar = fields.Integer(validate=Range(min=2, max=4))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["foo"]["exclusiveMinimum"] == 1
    assert props["foo"]["exclusiveMaximum"] == 3
    assert props["bar"]["minimum"] == 2
    assert props["bar"]["maximum"] == 4


def test_range_no_min_or_max():
    class SchemaNoMin(Schema):
        foo = fields.Integer(validate=validate.Range(max=4))

    class SchemaNoMax(Schema):
        foo = fields.Integer(validate=validate.Range(min=0))

    schema1 = SchemaNoMin()
    schema2 = SchemaNoMax()

    dumped1 = validate_and_dump(schema1)
    dumped2 = validate_and_dump(schema2)
    assert dumped1["definitions"]["SchemaNoMin"]["properties"]["foo"]["maximum"] == 4
    assert dumped2["definitions"]["SchemaNoMax"]["properties"]["foo"]["minimum"] == 0


def test_range_non_number_error():
    class TestSchema(Schema):
        foo = fields.String(validate=validate.Range(max=4))

    schema = TestSchema()

    json_schema = JSONSchema()

    with pytest.raises(UnsupportedValueError):
        json_schema.dump(schema)


def test_regexp():
    ipv4_regex = (
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
        r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
    )

    class TestSchema(Schema):
        ip_address = fields.String(validate=validate.Regexp(ipv4_regex))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["definitions"]["TestSchema"]["properties"]["ip_address"] == {
        "title": "ip_address",
        "type": "string",
        "pattern": ipv4_regex,
    }


def test_regexp_error():
    class TestSchema(Schema):
        test_regexp = fields.Int(validate=validate.Regexp(r"\d+"))

    schema = TestSchema()

    with pytest.raises(UnsupportedValueError):
        dumped = validate_and_dump(schema)


def test_custom_validator():
    class TestValidator(validate.Range):
        _jsonschema_base_validator_class = validate.Range

    class TestSchema(Schema):
        test_field = fields.Int(validate=TestValidator(min=1, max=10))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["definitions"]["TestSchema"]["properties"]
    assert props["test_field"]["minimum"] == 1
    assert props["test_field"]["maximum"] == 10
