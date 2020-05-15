from enum import Enum

from marshmallow_enum import EnumField

from jsonschema import Draft7Validator
from marshmallow import Schema, fields, validate
from marshmallow_jsonschema.compat import MARSHMALLOW_3

from marshmallow_jsonschema import JSONSchema
from marshmallow_jsonschema.compat import dot_data_backwards_compatible


class Address(Schema):
    id = fields.String(default="no-id")
    street = fields.String(required=True)
    number = fields.String(required=True)
    city = fields.String(required=True)
    floor = fields.Integer(validate=validate.Range(min=1, max=4))


class Color(Enum):
    RED = 1
    GREEN = 2
    YELLOW = 3


class TrafficStop(Schema):
    light_color = EnumField(Color)


class GithubProfile(Schema):
    uri = fields.String(required=True)


class UserSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    age = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(
        format="%Y-%m-%d", attribute="created", dump_only=True
    )
    created_iso = fields.DateTime(format="iso", attribute="created", dump_only=True)
    updated = fields.DateTime()
    species = fields.String(attribute="SPECIES")
    id = fields.String(default="no-id")
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Decimal()
    registered = fields.Boolean()
    hair_colors = fields.List(fields.Raw)
    sex_choices = fields.List(fields.Raw)
    finger_count = fields.Integer()
    uid = fields.UUID()
    time_registered = fields.Time()
    birthdate = fields.Date()
    since_created = fields.TimeDelta()
    sex = fields.Str(
        validate=validate.OneOf(
            choices=["male", "female", "non_binary", "other"],
            labels=["Male", "Female", "Non-binary/fluid", "Other"],
        )
    )
    various_data = fields.Dict()
    addresses = fields.Nested(
        Address, many=True, validate=validate.Length(min=1, max=3)
    )
    github = fields.Nested(GithubProfile)
    const = fields.String(validate=validate.Length(equal=50))


if MARSHMALLOW_3:
    UserSchema.updated_naive = fields.NaiveDateTime(attribute="updated", dump_only=True)


def _validate_schema(schema):
    """
    raises jsonschema.exceptions.SchemaError
    """
    Draft7Validator.check_schema(schema)


def validate_and_dump(schema):
    json_schema = JSONSchema()
    dumped = json_schema.dump(schema)
    data = dot_data_backwards_compatible(dumped)
    _validate_schema(data)
    # ensure last version
    assert data["$schema"] == "http://json-schema.org/draft-07/schema#"
    return data
