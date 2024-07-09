"""
Prototype for generating database entries from existing files

There is some re-writing of the files too, to make sure they have compliant metdata.
In production, this step would happen separately.
"""
from __future__ import annotations

from functools import partial
from pathlib import Path
from pprint import pprint

import pint_xarray  # noqa: F401
import xarray as xr

import input4mips_validation.xarray_helpers as iv_xr_helpers
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
)

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
CV_SOURCE_DIR = Path(__file__).parent / "../tests/test-data/cvs/input4MIPs/default"


working_files = [
    *ROOT_DATA_PATH.rglob("*mole-fraction-of-carbon-dioxide*.nc"),
    *ROOT_DATA_PATH.rglob("*mole-fraction-of-methane*.nc"),
]


raw_cvs_loader = get_raw_cvs_loader(cv_source=str(CV_SOURCE_DIR))
cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

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
        target_mip="CMIP",
        source_id="CR-CMIP-0-2-0",
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
    print()
    break
    print()
