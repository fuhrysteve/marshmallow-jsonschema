from marshmallow_jsonschema.base import JSONSchema


class ReactJsonSchemaFormJSONSchema(JSONSchema):
    """
    Usage (assuming marshmallow v3):

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
    json_schema, uischema = json_schema_obj.dump_with_uischema(MySchema())
    """

    def dump_with_uischema(self, obj, *, many=None):
        """Runs both dump and dump_uischema."""
        return self.dump(obj, many=many), self.dump_uischema(obj, many=many)

    def dump_uischema(self, obj, *, many=None):
        """
        Attempt to return something resembling a uiSchema compliant with
        react-jsonschema-form.

        See: https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
        """
        return dict(self._dump_uischema_iter(obj, many=many))

    def _dump_uischema_iter(self, obj, *, many=None):
        """
        Dictionary-iterator backing ``dump_uischema``. ``many`` is accepted
        for signature parity with ``dump`` but is currently unused — uiSchema
        layout doesn't change for many-style dumps.
        """
        del many  # accepted for signature parity, intentionally unused

        for k, v in getattr(obj.Meta, "react_uischema_extra", {}).items():
            yield k, v

        for field_name, field in obj.fields.items():
            # NOTE: doubled up to maintain backwards compatibility
            metadata = field.metadata.get("metadata", {})
            metadata.update(field.metadata)
            yield field_name, {k: v for k, v in metadata.items() if k.startswith("ui:")}
