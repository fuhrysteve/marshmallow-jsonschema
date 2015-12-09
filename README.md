## marshmallow-jsonschema: JSON Schema formatting with marshmallow

NOTE: This library does not yet have a stable API.
It is a prototype only still, and not intended for anything resembling production use.


[![Build Status](https://travis-ci.org/fuhrysteve/marshmallow-jsonschema.svg?branch=master)](https://travis-ci.org/fuhrysteve/marshmallow-jsonschema)

 marshmallow-jsonschema translates marshmallow schemas into
 JSON Schema Draft v4 compliant jsonschema. See http://json-schema.org/

### Why would I want my schema translated to JSON?

What are the use cases for this? Let's say you have a
marshmallow schema in python, but you want to render your
schema as a form in another system (for example: a web browser
or mobile device).

### Some Client tools can render forms using JSON Schema

* https://github.com/jdorn/json-editor
* https://github.com/ulion/jsonform


### Example usage

```python
from marshmallow_jsonschema import dump_schema
from tests import UserSchema

u = UserSchema()
dump_schema(u)
```
Yields:
```python
{'properties': {'age': {'title': 'age', 'type': 'number'},
  'balance': {'title': 'balance', 'type': 'number'},
  'birthdate': {'format': 'date', 'title': 'birthdate', 'type': 'string'},
  'created': {'format': 'date-time', 'title': 'created', 'type': 'string'},
  'created_formatted': {'format': 'date-time',
   'title': 'created',
   'type': 'string'},
  'created_iso': {'format': 'date-time', 'title': 'created', 'type': 'string'},
  'email': {'title': 'email', 'type': 'string'},
  'finger_count': {'title': 'finger_count', 'type': 'integer'},
  'hair_colors': {'title': 'hair_colors', 'type': 'array'},
  'homepage': {'title': 'homepage', 'type': 'string'},
  'id': {'default': 'no-id', 'title': 'id', 'type': 'string'},
  'name': {'title': 'name', 'type': 'string'},
  'registered': {'title': 'registered', 'type': 'boolean'},
  'sex': {'title': 'sex', 'type': 'string'},
  'sex_choices': {'title': 'sex_choices', 'type': 'array'},
  'since_created': {'title': 'since_created', 'type': 'string'},
  'species': {'title': 'SPECIES', 'type': 'string'},
  'time_registered': {'format': 'time',
   'title': 'time_registered',
   'type': 'string'},
  'uid': {'title': 'uid', 'type': 'string'},
  'updated': {'format': 'date-time', 'title': 'updated', 'type': 'string'},
  'updated_local': {'format': 'date-time',
   'title': 'updated',
   'type': 'string'},
  'various_data': {'title': 'various_data', 'type': 'object'}},
 'required': ['name'],
 'type': 'object'}
```
