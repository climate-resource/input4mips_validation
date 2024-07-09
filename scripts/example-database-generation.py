"""
Prototype for generating database entries from existing files

There is some re-writing of the files too, to make sure they have compliant metdata.
In production, this step would happen separately.
"""
from __future__ import annotations

import subprocess
from functools import partial
from pathlib import Path
from pprint import pprint

import cattrs.preconf.json
import iris
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
    *ROOT_DATA_PATH.rglob("*mole-fraction-of-carbon-dioxide*.nc"),
    *ROOT_DATA_PATH.rglob("*mole-fraction-of-methane*.nc"),
]


raw_cvs_loader = get_raw_cvs_loader(cv_source=str(CV_SOURCE_DIR))
cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)


@define
class DatasetEntry:
    """Data model for a single dataset entry"""

    activity_id: str
    """Activity ID that applies to the dataset"""

    contact: str
    """Email addresses to contact in case of questions about the dataset"""

    dataset_category: str
    """The dataset's category"""

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

    product: str
    """The kind of data that this dataset is"""

    # # Should be looked up from central CMIP stuff based on source_id, hence ignoring for now
    # source: str
    # """Longer name of the source that created the dataset"""

    source_id: str
    """Source ID that applies to the dataset"""

    variable_id: str
    """The ID of the variable contained in the dataset"""

    version: str
    """The version ID of the dataset"""


dataset_entries: list[DatasetEntry] = []

for wf in working_files:
    start = xr.load_dataset(wf, use_cftime=True)
    print(f"Working from {start}")

    new = start.sel(time=start.time.dt.year >= 1750).copy()  # noqa: PLR2004
    for bv in ["bounds", "sector_bounds", "time_bounds", "lat_bounds"]:
        if bv in new:
            new = new.drop_vars(bv)

    new.attrs = {}

    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
        grid_label=start.attrs["grid_label"],
        product="derived",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
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
    subprocess.run(["ncdump", "-h", str(out_file)], check=True)
    print()

    cube = iris.load_cube(out_file)
    iris_save_path = WRITING_DIR_IRIS / out_file.relative_to(WRITING_DIR)
    iris_save_path.parent.mkdir(parents=True, exist_ok=True)
    iris.save(cube, iris_save_path)
    written_iris = xr.load_dataset(iris_save_path, use_cftime=True)
    print(f"{written_iris=}")
    pprint(written_iris.attrs)
    subprocess.run(["ncdump", "-h", str(iris_save_path)], check=True)
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
    # - coordinates isn't allowed by CF conventions hence reading from an iris written file
    #   doesn't round trip nicely (xarray can't tell that bnds are not data variables)
    #   - using ncdata doesn't really help
    # break

db = [converter_json.unstructure(e) for e in dataset_entries]

with open(JSON_DB, "w") as fh:
    fh.write(json_dumps_cv_style(db))
