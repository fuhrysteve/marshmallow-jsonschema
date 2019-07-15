from marshmallow import fields


def handle_length(schema, field, validator, parent_schema):
    """Adds validation logic for ``marshmallow.validate.Length``, setting the
    values appropriately for ``fields.List``, ``fields.Nested``, and
    ``fields.String``.

    Args:
        schema (dict): The original JSON schema we generated. This is what we
            want to post-process.
        field (fields.Field): The field that generated the original schema and
            who this post-processor belongs to.
        validator (marshmallow.validate.Length): The validator attached to the
            passed in field.
        parent_schema (marshmallow.Schema): The Schema instance that the field
            belongs to.

    Returns:
        dict: A, possibly, new JSON Schema that has been post processed and
            altered.

    Raises:
        ValueError: Raised if the `field` is something other than
            `fields.List`, `fields.Nested`, or `fields.String`
    """
    if isinstance(field, fields.String):
        minKey = "minLength"
        maxKey = "maxLength"
    elif isinstance(field, (fields.List, fields.Nested)):
        minKey = "minItems"
        maxKey = "maxItems"
    else:
        raise ValueError(
            "In order to set the Length validator for JSON "
            "schema, the field must be either a List or a String"
        )

    if validator.min:
        schema[minKey] = validator.min

    if validator.max:
        schema[maxKey] = validator.max

    if validator.equal:
        schema[minKey] = validator.equal
        schema[maxKey] = validator.equal

    return schema


def handle_one_of(schema, field, validator, parent_schema):
    """Adds the validation logic for ``marshmallow.validate.OneOf`` by setting
    the JSONSchema `enum` property to the allowed choices in the validator.

    Args:
        schema (dict): The original JSON schema we generated. This is what we
            want to post-process.
        field (fields.Field): The field that generated the original schema and
            who this post-processor belongs to.
        validator (marshmallow.validate.OneOf): The validator attached to the
            passed in field.
        parent_schema (marshmallow.Schema): The Schema instance that the field
            belongs to.

    Returns:
        dict: A, possibly, new JSON Schema that has been post processed and
            altered.
    """
    if validator.choices:
        schema["enum"] = list(validator.choices)
        schema["enumNames"] = list(validator.labels)

    return schema


def handle_range(schema, field, validator, parent_schema):
    """Adds validation logic for ``marshmallow.validate.Range``, setting the
    values appropriately ``fields.Number`` and it's subclasses.

    Args:
        schema (dict): The original JSON schema we generated. This is what we
            want to post-process.
        field (fields.Field): The field that generated the original schema and
            who this post-processor belongs to.
        validator (marshmallow.validate.Length): The validator attached to the
            passed in field.
        parent_schema (marshmallow.Schema): The Schema instance that the field
            belongs to.

    Returns:
        dict: A, possibly, new JSON Schema that has been post processed and
            altered.
    """
    if not isinstance(field, fields.Number):
        return schema

    if validator.min:
        schema["minimum"] = validator.min

    if validator.max:
        schema["maximum"] = validator.max

    return schema
