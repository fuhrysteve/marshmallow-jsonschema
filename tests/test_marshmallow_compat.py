"""
Backward-compatibility test suite for marshmallow 3 and 4.

The same test inputs are dumped through `JSONSchema` and the resulting
schemas are compared against an exact expected shape - so a regression
on either marshmallow major version will fail loudly here, even if the
broader test suite still happens to pass.

Run on a marshmallow-3 environment and a marshmallow-4 environment to
demonstrate parity. The CI matrix in `.github/workflows/build.yml`
exercises both per push.
"""

from __future__ import annotations

import json
import uuid
from enum import Enum

import jsonschema
import pytest
from marshmallow import Schema, fields, validate

from marshmallow_jsonschema import JSONSchema, UnsupportedValueError
from marshmallow_jsonschema.base import ALLOW_NATIVE_ENUM, MARSHMALLOW_MAJOR

# --------------------------------------------------------------------------- #
# Version sniff itself                                                         #
# --------------------------------------------------------------------------- #


def test_marshmallow_major_is_three_or_four():
    """The compat shim must classify the installed marshmallow correctly.
    If this assertion ever fires for a major version we haven't planned
    for, we want a loud test failure, not a silent default."""
    assert MARSHMALLOW_MAJOR in (3, 4), MARSHMALLOW_MAJOR


def test_jsonschema_module_imports_cleanly():
    """The package must be importable with whatever marshmallow major is
    installed; this is the regression that forced the original 0.14.0
    pin."""
    import marshmallow_jsonschema

    assert marshmallow_jsonschema.JSONSchema is not None


# --------------------------------------------------------------------------- #
# Parity: identical inputs should produce identical schemas across versions    #
# --------------------------------------------------------------------------- #


def _strip_volatile(schema: dict) -> dict:
    """Output is already deterministic; this is a hook in case future
    versions start emitting wall-clock times or similar that we'd want
    to ignore for parity checks."""
    return schema


def test_simple_schema_parity():
    """A boring scalar schema is the cheapest sanity check that the
    cross-version shims haven't drifted on the happy path."""

    class S(Schema):
        username = fields.String()
        age = fields.Integer()
        balance = fields.Decimal()

    dumped = JSONSchema().dump(S())
    assert _strip_volatile(dumped) == {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$ref": "#/definitions/S",
        "definitions": {
            "S": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "age": {"title": "age", "type": "integer"},
                    "balance": {
                        "title": "balance",
                        "type": "number",
                        "format": "decimal",
                    },
                    "username": {"title": "username", "type": "string"},
                },
            }
        },
    }
    json.dumps(dumped)  # must round-trip


def test_required_fields_parity():
    class S(Schema):
        a = fields.String(required=True)
        b = fields.Integer()

    dumped = JSONSchema().dump(S())
    assert dumped["definitions"]["S"]["required"] == ["a"]


def test_dump_default_parity():
    """`dump_default` must be honored on both marshmallow versions
    (it was the deprecated-`default` rename in m3.13)."""

    class S(Schema):
        x = fields.String(dump_default="hello")

    dumped = JSONSchema().dump(S())
    assert dumped["definitions"]["S"]["properties"]["x"]["default"] == "hello"


def test_callable_default_skipped_parity():
    """Callable defaults must NOT be invoked at schema-gen time on
    either version - they're factories, not values."""

    class S(Schema):
        uid = fields.UUID(dump_default=uuid.uuid4)

    dumped = JSONSchema().dump(S())
    assert "default" not in dumped["definitions"]["S"]["properties"]["uid"]


def test_nonserializable_default_skipped_parity():
    """A non-callable, non-JSON-serializable default value (e.g. a
    UUID instance) must be silently dropped on both versions so
    downstream `json.dumps` doesn't crash."""

    class S(Schema):
        uid = fields.UUID(dump_default=uuid.uuid4())  # the value, not the factory

    dumped = JSONSchema().dump(S())
    assert "default" not in dumped["definitions"]["S"]["properties"]["uid"]
    json.dumps(dumped)


def test_metadata_parity():
    """`metadata={"title": ..., "description": ...}` overrides emit
    identically on both versions."""

    class S(Schema):
        x = fields.String(metadata={"title": "Custom Title", "description": "a thing"})

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["x"]
    assert prop["title"] == "Custom Title"
    assert prop["description"] == "a thing"


def test_dump_only_emits_readonly_parity():
    class S(Schema):
        secret = fields.String(dump_only=True)

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["secret"]
    assert prop["readOnly"] is True


def test_allow_none_on_scalar_parity():
    class S(Schema):
        x = fields.String(allow_none=True)

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["x"]
    assert prop["type"] == ["string", "null"]


def test_allow_none_on_nested_parity():
    class Inner(Schema):
        v = fields.Integer()

    class Outer(Schema):
        inner = fields.Nested(Inner, allow_none=True)

    prop = JSONSchema().dump(Outer())["definitions"]["Outer"]["properties"]["inner"]
    assert prop == {
        "anyOf": [
            {"type": "object", "$ref": "#/definitions/Inner"},
            {"type": "null"},
        ]
    }


def test_nested_recursive_parity():
    class Recursive(Schema):
        v = fields.Integer()
        children = fields.Nested("Recursive", many=True)

    dumped = JSONSchema().dump(Recursive())
    items = dumped["definitions"]["Recursive"]["properties"]["children"]["items"]
    assert items["$ref"] == "#/definitions/Recursive"


def test_data_key_used_as_property_name_parity():
    class S(Schema):
        snake_case = fields.String(data_key="camelCase", required=True)

    defn = JSONSchema().dump(S())["definitions"]["S"]
    assert "camelCase" in defn["properties"]
    assert "snake_case" not in defn["properties"]
    assert defn["required"] == ["camelCase"]


def test_oneof_validator_parity():
    class S(Schema):
        choice = fields.String(validate=validate.OneOf(["a", "b"], labels=["A", "B"]))

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["choice"]
    assert prop["enum"] == ["a", "b"]
    assert prop["enumNames"] == ["A", "B"]


def test_range_validator_parity():
    class S(Schema):
        n = fields.Integer(validate=validate.Range(min=1, min_inclusive=False, max=10))

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["n"]
    assert prop["exclusiveMinimum"] == 1
    assert prop["maximum"] == 10


def test_length_validator_parity():
    class S(Schema):
        s = fields.String(validate=validate.Length(min=1, max=255))

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["s"]
    assert prop["minLength"] == 1
    assert prop["maxLength"] == 255


def test_regexp_validator_parity():
    class S(Schema):
        s = fields.String(validate=validate.Regexp(r"^\d+$"))

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["s"]
    assert prop["pattern"] == r"^\d+$"


@pytest.mark.skipif(
    not ALLOW_NATIVE_ENUM, reason="needs marshmallow>=3.18 for native Enum field"
)
def test_native_enum_parity():
    """marshmallow 3.18+ and marshmallow 4 both ship the native Enum
    field; output must be identical."""
    from marshmallow.fields import Enum as NativeEnum

    class Color(Enum):
        RED = 1
        GREEN = 2

    class S(Schema):
        c = NativeEnum(Color)

    prop = JSONSchema().dump(S())["definitions"]["S"]["properties"]["c"]
    assert prop["type"] == "string"
    assert sorted(prop["enum"]) == ["GREEN", "RED"]


def test_constants_unknown_handling_parity():
    """`Meta.unknown` is set with INCLUDE/EXCLUDE/RAISE; both major
    marshmallow versions still expose these and they still flow through
    `_resolve_additional_properties`."""
    from marshmallow import EXCLUDE, INCLUDE, RAISE

    for value, expected in [(RAISE, False), (EXCLUDE, False), (INCLUDE, True)]:

        class S(Schema):
            class Meta:
                unknown = value

            x = fields.String()

        dumped = JSONSchema().dump(S())
        assert dumped["definitions"]["S"]["additionalProperties"] is expected


def test_schema_meta_title_and_description_parity():
    """Meta-level title/description (added in 0.15.0) must work on both."""

    class S(Schema):
        class Meta:
            title = "Title"
            description = "Description"

        x = fields.String()

    defn = JSONSchema().dump(S())["definitions"]["S"]
    assert defn["title"] == "Title"
    assert defn["description"] == "Description"


def test_definitions_path_parity():
    """The `definitions_path` reroute (added in 0.15.0) must work on both."""

    class Inner(Schema):
        x = fields.Integer()

    class Outer(Schema):
        inner = fields.Nested(Inner)

    dumped = JSONSchema(definitions_path="schemas").dump(Outer())
    assert "schemas" in dumped
    assert dumped["$ref"] == "#/schemas/Outer"


def test_props_ordered_parity():
    """`props_ordered=True` must preserve declaration order on both,
    including for nested schemas (regression for #109)."""

    class Inner(Schema):
        z = fields.String()
        a = fields.String()

    class Outer(Schema):
        d = fields.String()
        b = fields.String()
        nested = fields.Nested(Inner)

    dumped = JSONSchema(props_ordered=True).dump(Outer())
    assert list(dumped["definitions"]["Outer"]["properties"].keys()) == [
        "d",
        "b",
        "nested",
    ]
    assert list(dumped["definitions"]["Inner"]["properties"].keys()) == ["z", "a"]


# --------------------------------------------------------------------------- #
# Strong assertion: the generated schema validates real instances              #
# --------------------------------------------------------------------------- #


def test_generated_schema_validates_instances_parity():
    """End-to-end check: the schema we emit accepts valid input and
    rejects invalid input via a real JSON Schema validator. Catches
    drift where one version accidentally produces an over-permissive
    or malformed schema."""

    class S(Schema):
        name = fields.String(required=True)
        age = fields.Integer()

    dumped = JSONSchema().dump(S())

    jsonschema.validate({"name": "alice", "age": 30}, dumped)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"age": 30}, dumped)  # missing required `name`
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"name": "alice", "age": 1.5}, dumped)  # int vs float


def test_unsupported_field_raises_parity():
    """An unmapped custom field must raise `UnsupportedValueError` on
    both versions - silent fallback would hide bugs."""

    class Mystery(fields.Field):
        pass

    class S(Schema):
        x = Mystery()

    with pytest.raises(UnsupportedValueError):
        JSONSchema().dump(S())
