import marshmallow as ma

from marshmallow_jsonschema.extensions import ReactJsonSchemaFormJSONSchema


class MySchema(ma.Schema):
    first_name = ma.fields.String(metadata={"ui:autofocus": True})
    last_name = ma.fields.String()

    class Meta:
        react_uischema_extra = {"ui:order": ["first_name", "last_name"]}


def test_can_dump_react_jsonschema_form():
    json_schema_obj = ReactJsonSchemaFormJSONSchema()
    json_schema, uischema = json_schema_obj.dump_with_uischema(MySchema())
    assert uischema == {
        "first_name": {"ui:autofocus": True},
        "last_name": {},
        "ui:order": ["first_name", "last_name"],
    }
