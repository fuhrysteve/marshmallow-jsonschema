import datetime
import uuid
import decimal

from marshmallow import fields, missing, Schema, validate
from marshmallow.class_registry import get_class
from marshmallow.compat import text_type, binary_type, basestring

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

    @classmethod
    def _get_default_mapping(cls, obj):
        """Return default mapping if there are no special needs."""
        mapping = {v: k for k, v in obj.TYPE_MAPPING.items()}
        mapping.update({
            fields.Email: text_type,
            fields.Dict: dict,
            fields.Url: text_type,
            fields.List: list,
            fields.LocalDateTime: datetime.datetime,
            fields.Nested: '_from_nested_schema',
        })
        return mapping

    def get_properties(self, obj):
        mapping = self.__class__._get_default_mapping(obj)
        properties = {}

        for field_name, field in sorted(obj.fields.items()):
            schema = self.__class__._get_schema(obj, field)
            properties[field.name] = schema

        return properties

    def get_required(self, obj):
        required = []

        for field_name, field in sorted(obj.fields.items()):
            if field.required:
                required.append(field.name)

        return required

    @classmethod
    def _from_python_type(cls, obj, field, pytype):
        json_schema = {
            'title': field.attribute or field.name,
        }

        for key, val in TYPE_MAP[pytype].items():
            json_schema[key] = val

        if field.dump_only:
            json_schema['readonly'] = True

        if field.default is not missing:
            json_schema['default'] = field.default

        if field.metadata.get('metadata', {}).get('description'):
            json_schema['description'] = (
                field.metadata['metadata'].get('description')
            )

        if field.metadata.get('metadata', {}).get('title'):
            json_schema['title'] = field.metadata['metadata'].get('title')

        if isinstance(field, fields.List):
            json_schema['items'] = cls._get_schema(obj, field.container)
        return json_schema

    @classmethod
    def _get_schema(cls, obj, field):
        """Get schema and validators for field."""
        mapping = cls._get_default_mapping(obj)
        if hasattr(field, '_jsonschema_type_mapping'):
            schema = field._jsonschema_type_mapping()
        elif field.__class__ in mapping:
            pytype = mapping[field.__class__]
            if isinstance(pytype, basestring):
                schema = getattr(cls, pytype)(obj, field)
            else:
                schema = cls._from_python_type(
                    obj, field, pytype
                )
        else:
            raise ValueError('unsupported field type %s' % field)

        # Apply any and all validators that field may have
        for validator in field.validators:
            if validator.__class__ in FIELD_VALIDATORS:
                schema = FIELD_VALIDATORS[validator.__class__](
                    schema, field, validator, obj
                )
        return schema


    @classmethod
    def _from_nested_schema(cls, obj, field):
        if isinstance(field.nested, basestring):
            nested = get_class(field.nested)
        else:
            nested = field.nested
        schema = cls().dump(nested()).data

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
