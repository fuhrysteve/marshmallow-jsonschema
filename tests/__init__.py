import unittest

from marshmallow import Schema, fields, validate


class Address(Schema):
    id = fields.String(default='no-id')
    street = fields.String(required=True)
    number = fields.String(required=True)
    city = fields.String(required=True)
    floor = fields.Integer(validate=validate.Range(min=1, max=4))


class GithubProfile(Schema):
    uri = fields.String(required=True)


class UserSchema(Schema):
    name = fields.String(required=True,
                         validate=validate.Length(min=1, max=255))
    age = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(format="%Y-%m-%d", attribute="created")
    created_iso = fields.DateTime(format="iso", attribute="created")
    updated = fields.DateTime()
    updated_local = fields.LocalDateTime(attribute="updated")
    species = fields.String(attribute="SPECIES")
    id = fields.String(default='no-id')
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
    sex = fields.Str(validate=validate.OneOf(['male', 'female']))
    various_data = fields.Dict()
    addresses = fields.Nested(Address, many=True,
                              validate=validate.Length(min=1, max=3))
    github = fields.Nested(GithubProfile)
    const = fields.String(validate=validate.Length(equal=50))
    hex_number = fields.String(validate=validate.Regexp('^[a-fA-F0-9]+$'))


class BaseTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
