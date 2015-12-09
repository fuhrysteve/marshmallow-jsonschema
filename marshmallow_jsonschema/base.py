import datetime
import uuid
import decimal

from marshmallow import fields, missing


TYPE_MAP = {
    dict: {
        'type': 'object',
    },
    list: {
        'type': 'array',
    },
    datetime.time: {
        'type': 'string',
        'format': 'time',
    },
    datetime.timedelta: {
        # TODO explore using 'range'?
        'type': 'string',
    },
    datetime.datetime: {
        'type': 'string',
        'format': 'date-time',
    },
    datetime.date: {
        'type': 'string',
        'format': 'date',
    },
    uuid.UUID: {
        'type': 'string',
    },
    str: {
        'type': 'string',
    },
    bytes: {
        'type': 'string',
    },
    decimal.Decimal: {
        'type': 'number',
    },
    set: {
        'type': 'array',
    },
    tuple: {
        'type': 'array',
    },
    float: {
        'type': 'number',
    },
    int: {
        'type': 'integer',
    },
    bool: {
        'type': 'boolean',
    },
}


def dump_schema(schema_obj):
    json_schema = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    mapping = {v: k for k, v in schema_obj.TYPE_MAPPING.items()}
    mapping[fields.Email] = str
    mapping[fields.Dict] = dict
    mapping[fields.List] = list
    mapping[fields.Url] = str
    mapping[fields.LocalDateTime] = datetime.datetime
    for field_name, field in schema_obj.fields.items():
        python_type = mapping[field.__class__]
        json_schema['properties'][field.name] = {
            'title': field.attribute or field.name,
        }
        for key, val in TYPE_MAP[python_type].items():
            json_schema['properties'][field.name][key] = val
            
        if field.default is not missing:
            json_schema['properties'][field.name]['default'] = field.default
        if field.required:
            json_schema['required'].append(field.name)
    return json_schema
