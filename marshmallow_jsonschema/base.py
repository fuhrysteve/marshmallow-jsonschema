import datetime
import uuid
import decimal

from marshmallow import fields, missing, Schema, validate
from marshmallow.compat import text_type, binary_type

from .validation import handle_length, handle_one_of, handle_range


__all__ = ['JSONSchema']


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


FIELD_VALIDATORS = {
    validate.Length: handle_length,
    validate.OneOf: handle_one_of,
    validate.Range: handle_range,
}


class JSONSchema(Schema):
    properties = fields.Method('get_properties')
    type = fields.Constant('object')
    required = fields.Method('get_required')

    def get_properties(self, obj):
        mapping = {v: k for k, v in obj.TYPE_MAPPING.items()}
        mapping[fields.Email] = text_type
        mapping[fields.Dict] = dict
        mapping[fields.List] = list
        mapping[fields.Url] = text_type
        mapping[fields.LocalDateTime] = datetime.datetime
        properties = {}

        for field_name, field in sorted(obj.fields.items()):
            if hasattr(field, '_jsonschema_type_mapping'):
                schema = field._jsonschema_type_mapping()
            elif field.__class__ in mapping:
                pytype = mapping[field.__class__]
                schema = self.__class__._from_python_type(field, pytype)
            elif isinstance(field, fields.Nested):
                schema = self.__class__._from_nested_schema(field)
            else:
                raise ValueError('unsupported field type %s' % field)

            # Apply any and all validators that field may have
            for validator in field.validators:
                if validator.__class__ in FIELD_VALIDATORS:
                    schema = FIELD_VALIDATORS[validator.__class__](
                        schema, field, validator, obj
                    )

            properties[field.name] = schema

        return properties

    def get_required(self, obj):
        required = []

        for field_name, field in sorted(obj.fields.items()):
            if field.required:
                required.append(field.name)

        return required

    @classmethod
    def _from_python_type(cls, field, pytype):
        json_schema = {
            'title': field.attribute or field.name,
        }

        for key, val in TYPE_MAP[pytype].items():
            json_schema[key] = val

        if field.default is not missing:
            json_schema['default'] = field.default

        if field.metadata.get('metadata', {}).get('description'):
            json_schema['description'] = (
                field.metadata['metadata'].get('description')
            )

        if field.metadata.get('metadata', {}).get('title'):
            json_schema['title'] = field.metadata['metadata'].get('title')

        return json_schema

    @classmethod
    def _from_nested_schema(cls, field):
        schema = cls().dump(field.nested()).data

        if field.metadata.get('metadata', {}).get('description'):
            schema['description'] = (
                field.metadata['metadata'].get('description')
            )

        if field.metadata.get('metadata', {}).get('title'):
            schema['title'] = field.metadata['metadata'].get('title')

        if field.many:
            schema = {
                'type': ["array"] if field.required else ['array', 'null'],
                'items': schema,
            }

        return schema
