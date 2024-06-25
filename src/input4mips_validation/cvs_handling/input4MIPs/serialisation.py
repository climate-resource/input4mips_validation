"""
Serialisation for CVs handling
"""
from __future__ import annotations

import cattrs.preconf.json

converter_json = cattrs.preconf.json.make_converter()
