## marshmallow-jsonschema: JSON Schema formatting with marshmallow

[![Build Status](https://travis-ci.org/fuhrysteve/marshmallow-jsonschema.svg?branch=master)](https://travis-ci.org/fuhrysteve/marshmallow-jsonschema)

 marshmallow-jsonschema translates marshmallow schemas into
 JSON Schema Draft v4 compliant jsonschema. See http://json-schema.org/

### Why would I want my schema translated to JSON?

What are the use cases for this? Let's say you have a
marshmallow schema in python, but you want to render your
schema as a form in another system (for example: a web browser
or mobile device).

### Some Client tools can render forms using JSON Schema

https://github.com/jdorn/json-editor
https://github.com/ulion/jsonform


### Example usage

```python
from marshmallow_jsonschema.base import dump_schema
from tests import UserSchema

u = UserSchema()
dump_schema(u)
```
Yields:
```python
{'properties': {'age': {'required': False,
   'title': 'age',
   'type': {'type': 'number'}},
  'balance': {'required': False,
   'title': 'balance',
   'type': {'type': 'number'}},
  'birthdate': {'required': False,
   'title': 'birthdate',
   'type': {'format': 'date', 'type': 'string'}},
  'created': {'required': False,
   'title': 'created',
   'type': {'format': 'date-time', 'type': 'string'}},
  'created_formatted': {'required': False,
   'title': 'created',
   'type': {'format': 'date-time', 'type': 'string'}},
  'created_iso': {'required': False,
   'title': 'created',
   'type': {'format': 'date-time', 'type': 'string'}},
  'email': {'required': False, 'title': 'email', 'type': {'type': 'string'}},
  'finger_count': {'required': False,
   'title': 'finger_count',
   'type': {'type': 'integer'}},
  'hair_colors': {'required': False,
   'title': 'hair_colors',
   'type': {'type': 'array'}},
  'homepage': {'required': False,
   'title': 'homepage',
   'type': {'type': 'string'}},
  'id': {'default': 'no-id',
   'required': False,
   'title': 'id',
   'type': {'type': 'string'}},
  'name': {'required': False, 'title': 'name', 'type': {'type': 'string'}},
  'registered': {'required': False,
   'title': 'registered',
   'type': {'type': 'boolean'}},
  'sex': {'required': False, 'title': 'sex', 'type': {'type': 'string'}},
  'sex_choices': {'required': False,
   'title': 'sex_choices',
   'type': {'type': 'array'}},
  'since_created': {'required': False,
   'title': 'since_created',
   'type': {'type': 'string'}},
  'species': {'required': False,
   'title': 'SPECIES',
   'type': {'type': 'string'}},
  'time_registered': {'required': False,
   'title': 'time_registered',
   'type': {'format': 'time', 'type': 'string'}},
  'uid': {'required': False, 'title': 'uid', 'type': {'type': 'string'}},
  'updated': {'required': False,
   'title': 'updated',
   'type': {'format': 'date-time', 'type': 'string'}},
  'updated_local': {'required': False,
   'title': 'updated',
   'type': {'format': 'date-time', 'type': 'string'}},
  'various_data': {'required': False,
   'title': 'various_data',
   'type': {'type': 'object'}}},
 'type': 'object'}
```
