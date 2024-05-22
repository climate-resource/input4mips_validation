"""
Constants related to controlled vocabularies
"""
from __future__ import annotations

import re

# TODO: remove this hard-coding based on some logic/map held elsewhere,
# e.g. CVs website, that defines this map
VARIABLE_DATASET_MAP = {
    "tos": "SSTsAndSeaIce",
    "siconc": "SSTsAndSeaIce",
    "sftof": "SSTsAndSeaIce",
    "areacello": "SSTsAndSeaIce",
    "mole_fraction_of_carbon_dioxide_in_air": "GHGConcentrations",
    "mole_fraction_of_methane_in_air": "GHGConcentrations",
    "mole_fraction_of_nitrous_oxide_in_air": "GHGConcentrations",
    "mole_fraction_of_sulfur_hexafluoride_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc11_in_air": "GHGConcentrations",
}

# TODO: remove this hard-coding based on some logic/map held elsewhere,
# e.g. CVs website, that defines this map
VARIABLE_REALM_MAP = {
    "tos": "ocean",
    "siconc": "seaIce",
    "sftof": "ocean",
    "areacello": "ocean",
    "mole_fraction_of_carbon_dioxide_in_air": "atmos",
    "mole_fraction_of_methane_in_air": "atmos",
    "mole_fraction_of_nitrous_oxide_in_air": "atmos",
    "mole_fraction_of_sulfur_hexafluoride_in_air": "atmos",
    "mole_fraction_of_cfc11_in_air": "atmos",
}

CREATION_DATE_REGEX: re.Pattern[str] = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
"""
Regular expression that checks the creation date is formatted correctly
"""

UUID_REGEX: re.Pattern[str] = re.compile(
    r"^hdl:21.14100\/[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}$"
)
"""
Regular expression that checks the creation date is formatted correctly
"""

INCLUDES_EMAIL_REGEX: re.Pattern[str] = re.compile(r"^.*?(\S+@\S+\.\S+).*$")
"""
Regular expression that checks there is something like an email somewhere in the string

This is very loose and just provides a basic check to really avoid obvious
typos. It turns out writing a perfect regexp for email addresses is hard (see
e.g. https://stackoverflow.com/questions/201323/how-can-i-validate-an-email-address-using-a-regular-expression)
"""
