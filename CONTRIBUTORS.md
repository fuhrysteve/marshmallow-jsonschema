# Contributors

marshmallow-jsonschema exists because of the people below, who sent
patches, reported bugs, and pushed fixes upstream - often long before
the project had a clear response to them. A belated but heartfelt
thanks to everyone listed here.

## Major features and sustained contributions

- **Steve Pike (@stringfellow)** — landed the big recursive-nested rework with named definitions, `only`/`exclude` on nested schemas, custom enum labels (`enumNames`), serialization of field metadata, and `fields.Function` support (#37, #39, #47, #49, #51, #43).
- **Stanislav Rogovskiy (@atmo)** — modernized the codebase end-to-end: tox + Marshmallow 2 & 3 support, JSON Schema draft 7 logic for `Range`, `additionalProperties` support, allowing nested schemas as instances, a `validate_and_dump` test helper, black formatting, and pre-commit linting (#73, #74, #75, #76, #77, #78, #102).
- **Daniyar Yeralin (@yeralin)** — added `marshmallow.fields.Number` support, a hook to rename JSON Schema properties, subclass-based pytype detection, and pre-commit wiring (#80, #86, #88, #93).
- **kda47 (@kda47)** — fixed marshmallow-type subclass checks for datetime-based classes, added `Regexp` validator support, property-sort toggle, and restored Python 2.7 compatibility (#104).

## Field type support

- **Tomer Nosrati (@nusnuson)** — mapped `fields.IPInterface` to the JSON Schema types table (#155).
- **Shir Biton (@shirbi-cye)** — mapped `fields.IP` to the JSON Schema types table (#137).
- **Andreas Stenius (@kaos)** — fixed `UUID` field type detection to inherit from `String` (#144).
- **Thanathip Limna (@sdayu)** — added `items` output for `fields.List` (#31).
- **Ben Motz (@BenMotz)** — emitted type metadata for `Dict` values (#127).
- **Corey Dexter (@coreydexter)** — added support for `marshmallow_union` and `marshmallow_enum` third-party field types (#119).
- **Hadas Beker (@hadasarik)** — completed test coverage for the union and enum support work (merged alongside #119).
- **Konstantin Klein (@hf-kklein)** — added support for native `marshmallow.fields.Enum` in marshmallow 3.18+ (#170, later rebased into #189).

## Validator handlers

- **Eli Gundry (@eligundry)** — wrote the original Marshmallow validator support layer and the metadata-on-custom-fields path (#14, #21).
- **Erik Price (@erik)** — taught `handle_one_of` to accept any iterable and stabilized schema ordering across Python versions (#54).
- **J Axmacher (@jcaxmacher)** — first contributor to add a `Regexp` validator handler (#24).
- **Marcel Jackwerth (@mrcljx)** — added a handler for `validate.Equal` (#135).
- **Johan Groth (@jgroth)** — contributed the `anyOf` handler for `ContainsOnly` and the original `data_key`-as-property-name fix on behalf of Lundalogik (#96, #100).

## Nested schemas and definitions

- **Mouad Benchchaoui (@mouadino)** — landed the very first version of nested-field support and early polish (#3, #4).
- **Daniel Lindsäth (@alkanen)** — made nested schema class handling work across both Marshmallow 2.x and 3.x (#63).
- **Eduard Carreras (@ecarreras)** — fixed nested schema discovery to use `__class__` instead of reaching into internals (#59).
- **Alexander Graf (@ghostwheel42)** — propagated the marshmallow `context` dict into nested schemas during dumping (#160).
- **Chen Guo (@chenguo)** — extended `_jsonschema_type_mapping` to optionally receive the JSONSchema instance and schema object, unlocking wrapper-style custom fields (#165).
- **mrtedn21 (@mrtedn21)** — added the `definitions_path` constructor argument to support OpenAPI's `#/components/schemas/` convention (#179).
- **Sébastien De Fauw (@sdefauw)** — fixed `props_ordered` so it propagates to nested schemas (#129).
- **Gastón Avila (@avilaton)** — added `allow_none` handling for plain fields and then for `Nested` fields (#106, #122).

## Bug fixes

- **Jackson Toomey (@JacksonToomey)** — fixed the `int` Python type to emit `"integer"` instead of `"number"` in JSON Schema output (#152).
- **Ben Steadman (@SteadBytes)** — authored the jsonschema-validation regression test for integer fields (#118).
- **Noam Kush (@noamkush)** — stopped callable defaults from being emitted as schema defaults, added `default` for nested fields, and made the Makefile build/upload a wheel (#131, #151).
- **yuval-p (@yuval-p)** — surfaced the non-serializable-`default` issue that motivated the guard in #200 (#181).
- **Sidney Rubidge (@sidrubs)** — fixed the `readonly` property name to match the spec's `readOnly` (#147).
- **Martijn Thé (@martijnthe)** — used `data_key` (when set) as the JSON Schema property name (#139).
- **Smith Mathieu (@smith-m)** — earlier take on the `data_key`-as-property-name path, including title support and an unpinned jsonschema test dep (#65).
- **Stu Fisher (@stufisher)** — swapped the deprecated marshmallow `default` for `dump_default` (#167).
- **Nick McCartney (@namccart)** — aligned range-validation output with marshmallow's own validation behavior (#68).
- **Joshua Bryan (@jbryan)** — dropped empty `required` arrays to match JSON Schema draft-fge section 5.4.3 (#57).
- **Chris Targett (@xlevus)** — fixed array-of-object output so brutusin/json-forms accepts it (#44).
- **Hayden Chudy (@hjc)** — prevented `pypandoc` from breaking installs when not available (#15).
- **abcdenis (@abcdenis)** — fixed a buggy snippet in the colors README example (#126).
- **Stepland (@Stepland)** — quick compatibility patch for `_get_default_mapping` on marshmallow 3.0 (#90).

## Packaging, CI, docs

- **Danny Tiesling (@dtiesling)** — removed the deprecated `pkg_resources` dependency (#185).
- **Luke Marlin (@LukeMarlin)** — tightened up README wording and seeded the schema-level `title`/`description` metadata work later rebased into #200 (#97, #99).
- **Bart van der Schoor (@Bartvds)** — added Python 3.6 to Travis and trove classifiers, plus a regression test for a nested-list issue (#29, #30).
- **Steven Loria (@sloria)** — made `dump_schema` importable from the top level, switched to marshmallow's singleton `missing` sentinel, and cleaned up early example usage (#1, #2, #10).

---

If you contributed and your name is missing or your attribution is
off, please open an issue or PR and I will fix it.
