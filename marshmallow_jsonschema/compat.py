import sys

PY2 = int(sys.version_info[0]) == 2

if PY2:
    text_type = unicode
    binary_type = str
    basestring = basestring
else:
    text_type = str
    binary_type = bytes
    basestring = (str, bytes)


__all__ = (
    'text_type',
    'binary_type',
    'basestring',
)
