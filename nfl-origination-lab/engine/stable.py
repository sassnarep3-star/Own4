"""One JSON writer for the whole lab, so the bytes do not depend on the interpreter.

Python 3.12 changed float repr for some values relative to 3.11, which turns a
legitimate rebuild into a spurious diff. Every float is therefore rounded at the
source before it is written: any number this lab publishes is meaningful to at most
six decimals, and rounding at write time makes the output identical across CPython
versions and platforms. Nothing else is altered.
"""

import json


def _r(x, nd=12):
    if isinstance(x, float):
        return round(x, nd)
    if isinstance(x, dict):
        return {k: _r(v, nd) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_r(v, nd) for v in x]
    return x


def dump(obj, fh, indent=1):
    json.dump(_r(obj), fh, indent=indent)
    fh.write("\n")
