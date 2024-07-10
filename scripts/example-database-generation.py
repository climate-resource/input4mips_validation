"""
Prototype for generating database entries from existing files

There is some re-writing of the files too, to make sure they have compliant metdata.
In production, this step would happen separately.
"""

from __future__ import annotations

import json
import subprocess
from functools import partial
from pathlib import Path
from pprint import pprint

import cattrs.preconf.json
import cf_xarray.units  # noqa:F401 # get cf to format pint units
import iris
import pandas as pd
import pint_xarray  # noqa: F401
import xarray as xr
from attrs import define, fields

# from ncdata.iris_xarray import cubes_to_xarray, cubes_from_xarray
import input4mips_validation.xarray_helpers as iv_xr_helpers
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.serialisation import json_dumps_cv_style
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
)

converter_json = cattrs.preconf.json.make_converter()

iris.FUTURE.save_split_attrs = True

TMP_DATA_PATH = Path(__file__).parent / ".." / "tmp-data-downloaded-by-hand"
ROOT_DATA_PATH = (
    Path(__file__).parent
    / ".."
    / ".."
    / "CMIP-GHG-Concentration-Generation"
    / "output-bundles"
    / "20240524"
    / "data"
    / "processed"
    / "esgf-ready"
)
WRITING_DIR = Path(__file__).parent / ".." / "tmp-data"
WRITING_DIR_IRIS = Path(__file__).parent / ".." / "tmp-data-iris"
CV_SOURCE_DIR = Path(__file__).parent / "../tests/test-data/cvs/input4MIPs/default"

JSON_DB = WRITING_DIR_IRIS / "dataset_entries.json"


working_files = [
    *TMP_DATA_PATH.rglob("*.nc"),
    *ROOT_DATA_PATH.rglob("*mole-fraction-of-carbon-dioxide*.nc"),
    *ROOT_DATA_PATH.rglob("*mole-fraction-of-methane*.nc"),
]


raw_cvs_loader = get_raw_cvs_loader(cv_source=str(CV_SOURCE_DIR))
cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)


# Overall thinking/notes:
# - source ID is for dataset collection
# - dataset is for stuff that has e.g. specific grid, time end, time start
#     - something you could load with xr.load_mfdataset()
#
# - combine the stuff to create searchable tables
#     - need to work out the normal forms for this to be sensible
#
# - exclude
#     - status: that's a publishing thing, not something the dataset can know
#         - could go into a DataBaseEntry
#     - title: redundant
#     - all ESGF index stuff, that's a different database's problem/domain
#
# To add/edit from current required global attributes in main:
# - source_version
#   - just a renaming of version (version -> ESGF version,
#     source_version is version as defined by source)
#   - TODO: do this renaming
# - source
#   - Should be looked up from central CMIP stuff based on source_id,
#     hence ignoring for now
# - region
#   - CF conventions, so there are ways to check, just not obvious
# - table_id
#   - no idea what this is
#
# To add from reading Paul's data:
# - comment
#   - important for communication probably,
#     although maybe best managed outside the file?
# - data_specs_version
#   - no idea what this is
# - external_variables
#   - super important when we come to validate trees
# - grid
#   - seems redundant given grid_label, but ok
# - references
#   - useful
#
# To exclude from reading Paul's data:
# - release_year: totally redundant?
# - source_description: redundant given there is also source,
#   which is long-form source_id
# - source_type: redundant given there is product?
# - table_id: not used generally/not generally applicable?
# - table_info: not used generally?
# - cmor_version: not used generally?


@define
class DatasetEntry:
    """Data model for a single dataset entry"""

    Conventions: str
    """CF conventions used when writing the dataset"""

    activity_id: str
    """Activity ID that applies to the dataset"""

    contact: str
    """Email addresses to contact in case of questions about the dataset"""

    creation_date: str
    """Date the dataset was created"""

    dataset_category: str
    """The dataset's category"""

    datetime_end: str
    """The dataset's end time"""

    datetime_start: str
    """The dataset's starting time"""

    frequency: str
    """Frequency of the data in the dataset"""

    further_info_url: str
    """URL where further information about the dataset can be found"""

    grid_label: str
    """Grid label of the data in the dataset"""

    institution: str
    """Longer name of the institution that created the dataset"""

    institution_id: str
    """Institution ID of the institution that created the dataset"""

    license: str
    """License information for the dataset"""

    mip_era: str
    """The MIP era that applies to the dataset"""

    nominal_resolution: str
    """Nominal resolution of the data in the dataset"""

    product: str
    """The kind of data that this dataset is"""

    realm: str
    """The dataset's realm"""

    # # Should be looked up from central CMIP stuff based on source_id,
    # # hence ignoring for now
    # source: str
    # """Longer name of the source that created the dataset"""

    source_id: str
    """Source ID that applies to the dataset"""

    target_mip: str
    """The dataset's target MIP"""

    time_range: str
    """The dataset's time range"""

    tracking_id: str
    """Tracking ID of the dataset"""

    variable_id: str
    """The ID of the variable contained in the dataset"""

    version: str
    """The version ID of the dataset"""


# Re-writing the solar data
for wf in (Path(__file__).parent / ".." / "tmp-data-downloaded-by-hand-broken").rglob(
    "*.nc"
):
    subprocess.run(["ncdump", "-h", str(wf)], check=True)  # noqa: S603, S607
    start = xr.load_dataset(wf, use_cftime=True)
    print(f"Working from {start}")

    # See if raw data would work in terms of metadata
    dataset_entry_keys = [v.name for v in fields(DatasetEntry)]
    try:
        DatasetEntry(
            **{k: v for k, v in start.attrs.items() if k in dataset_entry_keys}
        )
    except TypeError as exc:
        print(exc)

    if "SOLARIS-HEPPA-CMIP-4-1" in start.attrs["source_id"]:
        for variable_name in start.variables:
            darray = start[variable_name]
            try:
                standard_name = darray.attrs["standard_name"]
            except KeyError:
                continue

            if variable_name in list(start.coords):
                continue

            ds = xr.Dataset({darray.attrs["standard_name"]: darray.pint.quantify()})
            ds.attrs = {}

            metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
                grid_label=start.attrs["grid_label"],
                nominal_resolution="tbd-cv",  # global-mean I guess
                # product should go into source_id
                product="tbd",  # need to check with Bernd
                source_id=start.attrs["source_id"],
                target_mip=start.attrs["target_mip"],
            )

            if start.attrs["frequency"] == "yr":
                add_time_bounds = partial(
                    iv_xr_helpers.add_time_bounds,
                    yearly_time_bounds=True,
                    monthly_time_bounds=False,
                )
            else:
                add_time_bounds = iv_xr_helpers.add_time_bounds

            ds = Input4MIPsDataset.from_data_producer_minimum_information(
                ds=ds,
                metadata_minimum=metadata_minimum,
                add_time_bounds=add_time_bounds,
                cvs=cvs,
            )
            out_file = ds.write(root_data_dir=WRITING_DIR)
            print()
            print(f"Wrote {out_file}")
            written = xr.load_dataset(out_file, use_cftime=True)
            print(f"{written=}")
            pprint(written.attrs)
            subprocess.run(["ncdump", "-h", str(out_file)], check=True)  # noqa: S603, S607
            print()

            cube = iris.load_cube(out_file)
            iris_save_path = WRITING_DIR_IRIS / out_file.relative_to(WRITING_DIR)
            iris_save_path.parent.mkdir(parents=True, exist_ok=True)
            iris.save(cube, iris_save_path)
            subprocess.run(["ncdump", "-h", str(iris_save_path)], check=True)  # noqa: S603, S607

    else:
        raise NotImplementedError(start.attrs["source_id"])


for wf in working_files:
    subprocess.run(["ncdump", "-h", str(wf)], check=True)  # noqa: S603, S607
    start = xr.load_dataset(wf, use_cftime=True)
    print(f"Working from {start}")

    new = start.sel(time=start.time.dt.year >= 1750).copy()  # noqa: PLR2004
    for bv in [
        "bounds",
        "sector_bounds",
        "time_bounds",
        "lat_bounds",
        "bnds",
        "time_bnds",
        "lat_bnds",
        "lon_bnds",
    ]:
        if bv in new:
            new = new.drop_vars(bv)

    new.attrs = {}

    if "CR" in start.attrs["source_id"]:
        metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
            source_id="CR-CMIP-0-2-0",
            target_mip="CMIP",
            # These should be inferable/checkable from CVs I think
            grid_label=start.attrs["grid_label"],
            nominal_resolution="tbd-cv",
            # product should go into source_id
            product="derived",
        )

    elif start.attrs["source_id"] == "PCMDI-AMIP-1-1-9":
        metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
            grid_label=start.attrs["grid_label"],
            nominal_resolution=start.attrs["nominal_resolution"],
            product=start.attrs["product"],
            source_id=start.attrs["source_id"],
            target_mip=start.attrs["target_mip"],
        )

    else:
        raise NotImplementedError(start.attrs["source_id"])

    if start.attrs["frequency"] == "yr":
        add_time_bounds = partial(
            iv_xr_helpers.add_time_bounds,
            yearly_time_bounds=True,
            monthly_time_bounds=False,
        )
    else:
        add_time_bounds = iv_xr_helpers.add_time_bounds

    ds = Input4MIPsDataset.from_data_producer_minimum_information(
        ds=new,
        metadata_minimum=metadata_minimum,
        add_time_bounds=add_time_bounds,
        cvs=cvs,
    )
    out_file = ds.write(root_data_dir=WRITING_DIR)
    print()
    print(f"Wrote {out_file}")
    written = xr.load_dataset(out_file, use_cftime=True)
    print(f"{written=}")
    pprint(written.attrs)
    subprocess.run(["ncdump", "-h", str(out_file)], check=True)  # noqa: S603, S607
    print()

    cube = iris.load_cube(out_file)
    iris_save_path = WRITING_DIR_IRIS / out_file.relative_to(WRITING_DIR)
    iris_save_path.parent.mkdir(parents=True, exist_ok=True)
    iris.save(cube, iris_save_path)


dataset_entries: list[DatasetEntry] = []

for file in WRITING_DIR_IRIS.rglob("*.nc"):
    written_iris = xr.load_dataset(file, use_cftime=True)
    print(f"{written_iris=}")
    pprint(written_iris.attrs)
    subprocess.run(["ncdump", "-h", str(iris_save_path)], check=True)  # noqa: S603, S607
    iris.load_cube(iris_save_path)
    print()
    print()

    dataset_entry_keys = [v.name for v in fields(DatasetEntry)]
    dataset_entry = DatasetEntry(
        **{k: v for k, v in written_iris.attrs.items() if k in dataset_entry_keys}
    )

    dataset_entries.append(dataset_entry)

    # Minor annoyances
    # - have to use iris for writing to get the CF conventions writing help
    #   - that requires only doing conda/pixi installs
    # - coordinates isn't allowed by CF conventions
    #   hence reading from an iris written file
    #   doesn't round trip nicely (xarray can't tell that bnds are not data variables)
    #   - using ncdata doesn't really help

db = [converter_json.unstructure(e) for e in dataset_entries]

with open(JSON_DB, "w") as fh:
    fh.write(json_dumps_cv_style(db))

with open(JSON_DB) as fh:
    df = pd.DataFrame(json.load(fh)).set_index("tracking_id")

# breakpoint()
