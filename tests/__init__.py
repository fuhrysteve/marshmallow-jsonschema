import unittest

from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    name = fields.String(required=True)
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


class BaseTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
