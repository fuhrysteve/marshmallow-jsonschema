from flask import Flask, jsonify
from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema

app = Flask(__name__)


class UserSchema(Schema):
    name = fields.String()
    address = fields.String()


@app.route("/schema")
def schema():
    schema = UserSchema()
    return jsonify(JSONSchema().dump(schema))


@app.route("/")
def home():
    return """<!DOCTYPE html>
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
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
