"""
Convert Paul's ESGF scraped data to a database
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import cattrs
import py7zr
from attrs import fields

from input4mips_validation.cvs_handling.input4MIPs.cvs_inference import (
    format_date_for_time_range,
)
from input4mips_validation.cvs_handling.serialisation import json_dumps_cv_style
from input4mips_validation.dataset import (
    Input4MIPsDatasetMetadataEntry,
    Input4MIPsDatasetMetadataFromESGF,
    Input4MIPsDatasetMetadataFromFiles,
)

converter_json = cattrs.preconf.json.make_converter()

IN_FILE = (
    Path(__file__).parent / ".." / ".." / "input4MIPs_CVs/src/231121_2147_comp.json.7z"
)
JSON_DB = "rewritten_dataset_entries.json"

with py7zr.SevenZipFile(IN_FILE, mode="r") as z:
    allfiles = z.getnames()
    z.extractall()


loaded_dicts = []
for file in allfiles:
    with open(file) as fh:
        loaded = json.load(fh)

    loaded_dicts.append(loaded)

if len(loaded_dicts) > 1:
    raise NotImplementedError()
start = loaded_dicts[0]

dataset_entries: list[Input4MIPsDatasetMetadataEntry] = []
for key, value in start.items():
    dataset_entry_keys = [v.name for v in fields(Input4MIPsDatasetMetadataFromFiles)]
    for k in sorted(value.keys()):
        print(f"{k}: {value[k]}")

    frequency = value["frequency"]
    if len(frequency) > 1:
        raise NotImplementedError()

    frequency = frequency[0]

    if "datetime_start" not in value:
        value["datetime_start"] = None

    if "datetime_stop" not in value:
        value["datetime_stop"] = None

    if frequency == "fx":
        if value["datetime_start"] is not None or value["datetime_stop"] is not None:
            # Values set incorrectly, overwrite
            value["datetime_start"] = None
            value["datetime_stop"] = None

        time_range = None

    elif value["datetime_start"] is None or value["datetime_stop"] is None:
        time_range = None

    else:
        if value["datetime_start"].startswith("0000"):
            start_time = format_date_for_time_range(
                dt.datetime.strptime(
                    value["datetime_start"].replace("0000", "0001"),
                    "%Y-%m-%dT%H:%M:%SZ",
                ),
                ds_frequency=frequency,
            )
            start_time = start_time.replace("0001", "0000")

        else:
            start_time = format_date_for_time_range(
                dt.datetime.strptime(value["datetime_start"], "%Y-%m-%dT%H:%M:%SZ"),
                ds_frequency=frequency,
            )

        end_time = format_date_for_time_range(
            dt.datetime.strptime(value["datetime_stop"], "%Y-%m-%dT%H:%M:%SZ"),
            ds_frequency=frequency,
        )
        time_range = f"{start_time}-{end_time}"

    if "target_mip" not in value and "target_mip_list" in value:
        value["target_mip"] = value["target_mip_list"]

    copy_across = {k: v for k, v in value.items() if k in dataset_entry_keys}
    copy_across_no_list = {}
    for k, v in copy_across.items():
        if isinstance(v, list) and len(v) > 1:
            if k == "target_mip":
                # Makes sense here probably
                copy_across_no_list[k] = v
                continue

            raise NotImplementedError(k)

        if isinstance(v, list):
            copy_across_no_list[k] = v[0]
        else:
            copy_across_no_list[k] = v

    for maybe_missing in [
        "contact",
        "dataset_category",
        "further_info_url",
        "nominal_resolution",
        "product",
        "source_version",
    ]:
        if maybe_missing not in copy_across_no_list:
            # Bad bad, including data I helped make i.e. the future GHG conc
            copy_across_no_list[maybe_missing] = None

    dataset_entry_files = Input4MIPsDatasetMetadataFromFiles(
        **{
            **copy_across_no_list,
            "creation_date": value["_timestamp"],
            "datetime_end": value["datetime_stop"],
            "license": "not_in_esgf",
            "license_id": "not_in_esgf",
            "region": "not_in_esgf",
            "time_range": time_range,
            "tracking_id": value["pid"] if "pid" in value else None,
        }
    )

    if "xlink" not in value and "url" in value:
        value["xlink"] = value["url"]

    esgf_keys = [v.name for v in fields(Input4MIPsDatasetMetadataFromESGF)]
    esgf_entries = {k: v for k, v in value.items() if k in esgf_keys}

    for v in esgf_entries["xlink"]:
        if "cera-www.dkrz.de" in v:
            xlink = v.split("|")[0]
            break

        if "hdl.handle" in v:
            xlink = v.split("|")[0]
            break

        if "aims3.llnl.gov" in v:
            xlink = v.split("|")[0]
            break

    else:
        raise NotImplementedError()

    dataset_entry_esgf = Input4MIPsDatasetMetadataFromESGF(
        **{**esgf_entries, "xlink": xlink, "timestamp": value["_timestamp"]}
    )

    dataset_entry = Input4MIPsDatasetMetadataEntry(
        file=dataset_entry_files,
        esgf=dataset_entry_esgf,
    )

    dataset_entries.append(dataset_entry)

db = [converter_json.unstructure(e) for e in dataset_entries]

with open(JSON_DB, "w") as fh:
    fh.write(json_dumps_cv_style(db))
