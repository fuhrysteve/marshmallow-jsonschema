import importlib
import marshmallow_jsonschema


def test_import_marshmallow_union(monkeypatch):
    monkeypatch.delattr("marshmallow_union.Union")

    base = importlib.reload(marshmallow_jsonschema.base)

    assert not base.ALLOW_UNIONS

    monkeypatch.undo()

    importlib.reload(marshmallow_jsonschema.base)


def test_import_marshmallow_enum(monkeypatch):
    monkeypatch.delattr("marshmallow_enum.EnumField")

    base = importlib.reload(marshmallow_jsonschema.base)

    assert not base.ALLOW_ENUMS

    monkeypatch.undo()

    importlib.reload(marshmallow_jsonschema.base)
