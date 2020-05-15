import pytest

from . import Color, TrafficStop, validate_and_dump


def test_enum_dump_validate_schema():

    schema = TrafficStop()
    dumped = validate_and_dump(schema)
    props = dumped["definitions"]["TrafficStop"]["properties"]

    assert props['light_color']['enum'] == ['RED', 'GREEN', 'YELLOW']
    assert props['light_color']['type'] == 'string'