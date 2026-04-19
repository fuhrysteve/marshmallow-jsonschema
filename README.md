# marshmallow-jsonschema: JSON Schema formatting with marshmallow

![Build Status](https://github.com/fuhrysteve/marshmallow-jsonschema/workflows/build/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

`marshmallow-jsonschema` translates [marshmallow](https://marshmallow.readthedocs.io/)
schemas into [JSON Schema Draft v7](http://json-schema.org/) compliant
documents.

## Why would I want my schema translated to JSON?

A few common reasons:

- Render a marshmallow schema as a form in another runtime (web browser,
  mobile, native desktop) where you can't import Python.
- Validate request/response bodies in an API gateway or contract-test
  layer that consumes JSON Schema directly.
- Publish your schema as documentation alongside an OpenAPI spec.

## Installation

Requires Python 3.9+ and marshmallow 3.13 or later (works on both
marshmallow 3 and marshmallow 4).

```
pip install marshmallow-jsonschema
```

For older environments:

- marshmallow 2 → `marshmallow-jsonschema<0.11`
- Python 3.6–3.8 or marshmallow 3.11–3.12 → `marshmallow-jsonschema<0.14`
- A marshmallow-4-broken intermediate state → `marshmallow-jsonschema<0.14` (with `marshmallow<4`)

## Client tools that render forms from JSON Schema

- [react-jsonschema-form](https://github.com/rjsf-team/react-jsonschema-form) (recommended) — see the React extension below.
- [json-editor](https://github.com/json-editor/json-editor)
- [brutusin/json-forms](https://github.com/brutusin/json-forms) (legacy; the maintained alternatives above are usually better today)

## Examples

### Simple example

```python
from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema

class UserSchema(Schema):
    username = fields.String()
    age = fields.Integer()
    birthday = fields.Date()

JSONSchema().dump(UserSchema())
```

Yields:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$ref": "#/definitions/UserSchema",
    "definitions": {
        "UserSchema": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
                "age": {"title": "age", "type": "integer"},
                "birthday": {"title": "birthday", "type": "string", "format": "date"},
                "username": {"title": "username", "type": "string"}
            }
        }
    }
}
```

### Nested example

Nested schemas land in `definitions` and are referenced via `$ref`:

```python
from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema

class AddressSchema(Schema):
    street = fields.String()
    city = fields.String()

class UserSchema(Schema):
    name = fields.String()
    address = fields.Nested(AddressSchema)

JSONSchema().dump(UserSchema())
```

Yields:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$ref": "#/definitions/UserSchema",
    "definitions": {
        "AddressSchema": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
                "city": {"title": "city", "type": "string"},
                "street": {"title": "street", "type": "string"}
            }
        },
        "UserSchema": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
                "address": {"type": "object", "$ref": "#/definitions/AddressSchema"},
                "name": {"title": "name", "type": "string"}
            }
        }
    }
}
```

`fields.Nested("Self")` and `fields.Nested(lambda: SomeSchema())` are
both supported for recursive references.

### Flask + JSON Schema form rendering

A complete runnable Flask example that exposes a marshmallow schema as
JSON Schema and renders it as a form lives at [`example/example.py`](example/example.py).
That example uses [brutusin/json-forms](https://github.com/brutusin/json-forms)
on the JS side; for a more current alternative, see the
[React-JSONSchema-Form Extension](#react-jsonschema-form-extension)
section below.

## Validators

Marshmallow's standard validators translate automatically into JSON
Schema constraints when the field is dumped:

| Validator | JSON Schema output |
|---|---|
| `validate.Length(min=, max=)` | `minLength` / `maxLength` for strings, `minItems` / `maxItems` for lists & nested |
| `validate.Range(min=, max=, min_inclusive=, max_inclusive=)` | `minimum` / `maximum` (or `exclusiveMinimum` / `exclusiveMaximum`) |
| `validate.OneOf(choices, labels=)` | `enum` (and the non-standard `enumNames` for compatibility with `react-jsonschema-form`) |
| `validate.Equal(value)` | `enum: [value]` |
| `validate.Regexp(pattern)` | `pattern` |
| `validate.ContainsOnly(choices, labels=)` | `items.anyOf: [{const}, ...]` + `uniqueItems: true` |

```python
from marshmallow import Schema, fields, validate
from marshmallow_jsonschema import JSONSchema

class UserSchema(Schema):
    age = fields.Integer(validate=validate.Range(min=0, max=150))
    name = fields.String(validate=validate.Length(min=1, max=100))
    role = fields.String(validate=validate.OneOf(["admin", "user"]))
```

For a custom validator that's a subclass of one of the above, set
`_jsonschema_base_validator_class = validate.<Base>` on it so the
translation still fires.

## Enums

`marshmallow.fields.Enum` (added in marshmallow 3.18) is supported
out of the box and emits the enum-member names. The third-party
[marshmallow-enum](https://pypi.org/project/marshmallow-enum/)
`EnumField` is also supported when installed; native Enum is preferred
when both are present.

## Advanced usage

### Schema-level title and description

Setting `title` or `description` on a schema's inner `Meta` class
emits them at the corresponding definition entry:

```python
class UserSchema(Schema):
    class Meta:
        title = "User"
        description = "A user account record."

    name = fields.String()
```

### Customizing the `definitions` path

By default nested schemas live under `#/definitions/<Name>`. Pass
`definitions_path` to use a different single-segment key:

```python
JSONSchema(definitions_path="schemas").dump(MySchema())
# {"$ref": "#/schemas/MySchema", "schemas": {...}, ...}
```

Multi-segment paths (e.g. `"components/schemas"`) are rejected because
they would produce a flat dict key with a slash in it rather than the
nested structure consumers expect — wrap the output yourself if you
need that shape.

### Custom field types

Add a `_jsonschema_type_mapping` method to your field so we know how
to serialize it. Field-level `metadata={...}` and `dump_default`
values are then merged in automatically, so a single mapping method
gets you the full set of standard schema attributes.

```python
class Colour(fields.Field):
    def _jsonschema_type_mapping(self):
        return {"type": "string"}

    def _serialize(self, value, attr, obj):
        r, g, b = value
        return "#%02X%02X%02X" % (r, g, b)


class UserSchema(Schema):
    favourite_colour = Colour(
        dump_default="#ffffff",
        metadata={"title": "Colour", "description": "Hex RGB"},
    )
```

For wrapper-style custom fields that need to re-enter the dumping
machinery (e.g. to emit a `$ref` to a recursive schema), declare
`_jsonschema_type_mapping(self, json_schema, obj)` with the two extra
parameters and the `JSONSchema` instance + obj will be passed in.

### React-JSONSchema-Form Extension

[react-jsonschema-form](https://rjsf-team.github.io/react-jsonschema-form/)
renders JSON Schema as a React form. It accepts a separate
[`uiSchema`](https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema)
that controls presentation; this package's
`ReactJsonSchemaFormJSONSchema` extension dumps both at once:

```python
from marshmallow import Schema, fields
from marshmallow_jsonschema.extensions import ReactJsonSchemaFormJSONSchema

class MySchema(Schema):
    first_name = fields.String(metadata={"ui:autofocus": True})
    last_name = fields.String()

    class Meta:
        react_uischema_extra = {"ui:order": ["first_name", "last_name"]}


json_schema_obj = ReactJsonSchemaFormJSONSchema()
data = json_schema_obj.dump(MySchema())
ui_schema_json = json_schema_obj.dump_uischema(MySchema())
```

## Contributing

Bug reports and pull requests are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) for local-dev setup and
[CONTRIBUTORS.md](CONTRIBUTORS.md) for the people who built this.
