## marshmallow-jsonschema: JSON Schema formatting with marshmallow

[![Build Status](https://travis-ci.org/fuhrysteve/marshmallow-jsonschema.svg?branch=master)](https://travis-ci.org/fuhrysteve/marshmallow-jsonschema)
[![Coverage Status](https://coveralls.io/repos/github/fuhrysteve/marshmallow-jsonschema/badge.svg?branch=master)](https://coveralls.io/github/fuhrysteve/marshmallow-jsonschema?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

 marshmallow-jsonschema translates marshmallow schemas into
 JSON Schema Draft v7 compliant jsonschema. See http://json-schema.org/

#### Why would I want my schema translated to JSON?

What are the use cases for this? Let's say you have a
marshmallow schema in python, but you want to render your
schema as a form in another system (for example: a web browser
or mobile device).

#### Installation

```
pip install marshmallow-jsonschema
```

#### Some Client tools can render forms using JSON Schema

* [react-jsonschema-form](https://github.com/mozilla-services/react-jsonschema-form) (recommended)
 * See below extension for this excellent library!
* https://github.com/brutusin/json-forms
* https://github.com/jdorn/json-editor
* https://github.com/ulion/jsonform

### Examples

Note that while these examples are using marshmallow v3 API, marshmallow v2 is
also still supported and part of the build. Support will be dropped for v2 in a future release.

#### Simple Example

```python
from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema

class UserSchema(Schema):
    username = fields.String()
    age = fields.Integer()
    birthday = fields.Date()

user_schema = UserSchema()

json_schema = JSONSchema()
json_schema.dump(user_schema)
```
Yields:
```python
{'properties': {'age': {'format': 'integer',
                        'title': 'age',
                        'type': 'number'},
                'birthday': {'format': 'date',
                             'title': 'birthday',
                             'type': 'string'},
                'username': {'title': 'username', 'type': 'string'}},
 'required': [],
 'type': 'object'}
```

#### Nested Example

```python
from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema
from tests import UserSchema


class Athlete(object):
    user_schema = UserSchema()

    def __init__(self):
        self.name = 'sam'


class AthleteSchema(Schema):
    user_schema = fields.Nested(JSONSchema)
    name = fields.String()

    
athlete = Athlete()
athlete_schema = AthleteSchema()

athlete_schema.dump(athlete)
```

#### Complete example Flask application using brutisin/json-forms

![Screenshot](http://i.imgur.com/jJv1wFk.png)

This example renders a form not dissimilar to how [wtforms](https://github.com/wtforms/wtforms) might render a form.

However rather than rendering the form in python, the JSON Schema is rendered using the
javascript library [brutusin/json-forms](https://github.com/brutusin/json-forms).


```python
from flask import Flask, jsonify
from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema

app = Flask(__name__)


class UserSchema(Schema):
    name = fields.String()
    address = fields.String()


@app.route('/schema')
def schema():
    schema = UserSchema()
    return jsonify(JSONSchema().dump(schema))


@app.route('/')
def home():
    return '''<!DOCTYPE html>
<head>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/brutusin.json-forms/1.3.0/css/brutusin-json-forms.css"><Paste>
<script src="https://code.jquery.com/jquery-1.12.1.min.js" integrity="sha256-I1nTg78tSrZev3kjvfdM5A5Ak/blglGzlaZANLPDl3I=" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/underscore.string/3.3.4/underscore.string.min.js"></script>
<script src="https://cdn.jsdelivr.net/brutusin.json-forms/1.3.0/js/brutusin-json-forms.min.js"></script>
<script>
$(document).ready(function() {
    $.ajax({
        url: '/schema'
        , success: function(data) {
            var container = document.getElementById('myform');
            var BrutusinForms = brutusin["json-forms"];
            var bf = BrutusinForms.create(data);
            bf.render(container);
        }
    });
});
</script>
</head>
<body>
<div id="myform"></div>
</body>
</html>
'''


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

```


### Advanced usage
#### Adding metadata on schemas
It is possible to define metadata on schema definition.
So far, three of them are supported:
 * description
 * title
 * additional_properties (results in additionalProperties when dumped)

To use them, you need to provide a `Meta` inner class to your `Schema` with the respective properties:

```python
class MySchema(Schema):
    class Meta:
        additional_properties = True
        title = "A nice title"
        description = "A lengthy description"
    a_field = fields.String()
```

#### Custom Type support

Simply add a `_jsonschema_type_mapping` method to your field
so we know how it ought to get serialized to JSON Schema.

A common use case for this is creating a dropdown menu using
enum (see Gender below).


```python
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

class Gender(fields.String):
    def _jsonschema_type_mapping(self):
        return {
            'type': 'string',
            'enum': ['Male', 'Female']
        }


class UserSchema(Schema):
    name = fields.String(required=True)
    favourite_colour = Colour()
    gender = Gender()

schema = UserSchema()
json_schema = JSONSchema()
json_schema.dump(schema)
```


### React-JSONSchema-Form Extension

[react-jsonschema-form](https://react-jsonschema-form.readthedocs.io/en/latest/)
is a library for rendering jsonschemas as a form using React. It is very powerful
and full featured.. the catch is that it requires a proprietary
[`uiSchema`](https://react-jsonschema-form.readthedocs.io/en/latest/form-customization/#the-uischema-object)
to provide advanced control how the form is rendered.
[Here's a live playground](https://rjsf-team.github.io/react-jsonschema-form/)

*(new in version 0.10.0)*

```python
from marshmallow_jsonschema.extensions import ReactJsonSchemaFormJSONSchema

class MySchema(Schema):
    first_name = fields.String(
        metadata={
            'ui:autofocus': True,
        }
    )
    last_name = fields.String()

    class Meta:
        react_uischema_extra = {
            'ui:order': [
                'first_name',
                'last_name',
            ]
        }


json_schema_obj = ReactJsonSchemaFormJSONSchema()
schema = MySchema()

# here's your jsonschema
data = json_schema_obj.dump(schema)

# ..and here's your uiSchema!
ui_schema_json = json_schema_obj.dump_uischema(schema)
```
