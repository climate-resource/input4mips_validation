"""
Prototype for validating data entries
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cattrs
import pandas as pd
import xarray as xr

from input4mips_validation.cvs_handling.serialisation import json_dumps_cv_style
from input4mips_validation.dataset import Input4MIPsDatasetMetadataEntry
from input4mips_validation.validation import validate_file

converter_json = cattrs.preconf.json.make_converter()

WRITTEN_DIR = Path(__file__).parent / ".." / "tmp-data-iris"
JSON_DB = WRITTEN_DIR / "dataset_entries.json"

dataset_entries: list[Input4MIPsDatasetMetadataEntry] = []

# for wf in (Path(__file__).parent / ".." / "tmp-data-downloaded-by-hand-broken").rglob(
#     "*.nc"
# ):
#     written = xr.load_dataset(wf, use_cftime=True)
#     subprocess.run(["ncdump", "-h", str(wf)], check=True)
#
#     validate_file(wf)

for file in WRITTEN_DIR.rglob("*.nc"):
    written = xr.load_dataset(file, use_cftime=True)
    subprocess.run(["ncdump", "-h", str(file)], check=True)  # noqa: S603, S607

    dataset_entry = validate_file(file)

    dataset_entries.append(dataset_entry)

db = [converter_json.unstructure(e) for e in dataset_entries]

with open(JSON_DB, "w") as fh:
    fh.write(json_dumps_cv_style(db))

with open(JSON_DB) as fh:
    raw = json.load(fh)
    df = pd.DataFrame([{**v["file"], **v["esgf"]} for v in raw]).set_index(
        "tracking_id"
    )

print(df)
# breakpoint()
