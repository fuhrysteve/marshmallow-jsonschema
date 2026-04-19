"""
Minimal Flask example: dump a marshmallow schema as JSON Schema and
render it as a form using json-editor (https://github.com/json-editor/json-editor).

Run locally:

    pip install -r example/requirements.txt
    python example/example.py
    open http://127.0.0.1:5000/

This is purely an exploration aid - the inline HTML / CDN approach is
fine for that and intentionally avoids a JS build pipeline.
"""

from flask import Flask, jsonify
from marshmallow import Schema, fields, validate

from marshmallow_jsonschema import JSONSchema

app = Flask(__name__)


class AddressSchema(Schema):
    class Meta:
        title = "Address"

    street = fields.String(required=True)
    city = fields.String(required=True)


class UserSchema(Schema):
    class Meta:
        title = "User"
        description = "Sign up for an account."

    name = fields.String(required=True, metadata={"description": "Your full name"})
    age = fields.Integer(validate=validate.Range(min=18, max=150))
    role = fields.String(validate=validate.OneOf(["user", "admin"]))
    address = fields.Nested(AddressSchema)


@app.route("/schema")
def schema():
    return jsonify(JSONSchema().dump(UserSchema()))


# Pin the json-editor version so this example doesn't silently break
# when the upstream library ships a backwards-incompatible change.
_JSON_EDITOR_VERSION = "2.15.1"

INDEX_HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>marshmallow-jsonschema example</title>
<script src="https://cdn.jsdelivr.net/npm/@json-editor/json-editor@{_JSON_EDITOR_VERSION}/dist/jsoneditor.min.js"></script>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 720px; margin: 2em auto; padding: 0 1em; }}
</style>
</head>
<body>
<h1>marshmallow-jsonschema example</h1>
<p>The form below was generated from a marshmallow <code>Schema</code>.
   The schema is served as JSON at <a href="/schema">/schema</a>.</p>
<div id="editor"></div>
<script>
fetch('/schema')
    .then(function (r) {{ return r.json(); }})
    .then(function (schema) {{
        new JSONEditor(document.getElementById('editor'), {{
            schema: schema,
            theme: 'html'
        }});
    }});
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return INDEX_HTML


if __name__ == "__main__":
    # Local exploration only. Never run Flask with debug=True in
    # production - it exposes the Werkzeug debugger.
    app.run(host="127.0.0.1")
