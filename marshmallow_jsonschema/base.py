import datetime
import uuid
import decimal

from marshmallow import fields, missing
from marshmallow.compat import text_type, binary_type


__all__ = ['dump_schema']


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
        'format': 'uuid',
    },
    text_type: {
        'type': 'string',
    },
    binary_type: {
        'type': 'string',
    },
    decimal.Decimal: {
        'type': 'number',
        'format': 'decimal',
    },
    set: {
        'type': 'array',
    },
    tuple: {
        'type': 'array',
    },
    float: {
        'type': 'number',
        'format': 'float',
    },
    int: {
        'type': 'number',
        'format': 'integer',
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
    mapping[fields.Email] = text_type
    mapping[fields.Dict] = dict
    mapping[fields.List] = list
    mapping[fields.Url] = text_type
    mapping[fields.LocalDateTime] = datetime.datetime
    for field_name, field in sorted(schema_obj.fields.items()):
        if field.__class__ in mapping:
            pytype = mapping[field.__class__]
            schema = _from_python_type(field, pytype)
        elif isinstance(field, fields.Nested):
            schema = _from_nested_schema(field)
        else:
            raise ValueError('unsupported field type %s' % field)
        json_schema['properties'][field.name] = schema
        if field.required:
            json_schema['required'].append(field.name)
    return json_schema


def _from_python_type(field, pytype):
    json_schema = {
        'title': field.attribute or field.name,
    }
    for key, val in TYPE_MAP[pytype].items():
        json_schema[key] = val
    if field.default is not missing:
        json_schema['default'] = field.default

    return json_schema


def _from_nested_schema(field):
    schema = dump_schema(field.nested())
    if field.many:
        schema = {
            'type': ["array"] if field.required else ['array', 'null'],
            'items': schema
        }
    return schema
