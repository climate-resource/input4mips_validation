"""
Add input4MIPs information to the raw MAC-SPv2 file
"""

from __future__ import annotations

from pathlib import Path

import cftime
import iris
import ncdata
import numpy as np
import xarray as xr
from loguru import logger

from input4mips_validation.cvs import load_cvs
from input4mips_validation.cvs.cvs import Input4MIPsCVs
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadata,
)
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
)
from input4mips_validation.validation.file import get_validate_file_result
from input4mips_validation.xarray_helpers import add_time_bounds


def main(  # noqa: PLR0913
    raw_file: Path,
    output_dir: Path,
    cvs: Input4MIPsCVs,
    input4mips_metadata: Input4MIPsDatasetMetadata,
    non_input4mips_metadata: dict[str, str],
    years_to_keep: list[int],
) -> None:
    """
    Re-write the file
    """
    ds_raw = xr.load_dataset(raw_file)

    # Update non-input4MIPs metadata
    non_input4mips_metadata = {
        "references": "https://doi.org/10.5194/gmd-10-433-2017",
    }
    for key in ["History", "Author", "Reference"]:
        non_input4mips_metadata[key.lower()] = ds_raw.attrs[key]

    non_input4mips_metadata["history"] = (
        f"{non_input4mips_metadata['history']}. "
        "Written into ESGF format with `add-input4mips-info-to-mac.py`."
    )

    # Only write out years which are relevant
    ds_out = ds_raw.sel(years=years_to_keep).copy()

    # Fix up mislabelling of features so that they are in line with
    # the indexing in the paper: Stevens et al., GMD 2017 (doi:10.5194/gmd-10-433-2017)
    ds_out["plume_feature"] = range(1, 1 + ds_out["plume_feature"].size)

    # Rename year fraction
    ds_out = ds_out.rename({"year_fr": "year_fraction"})

    # Convert years to a standard time axis
    ds_out = ds_out.rename({"years": "time"})
    ds_out["time"] = [cftime.DatetimeNoLeap(y, 7, 2) for y in ds_out["time"]]

    # Create a region variable for holding the region names
    regions = np.array(
        [
            ds_raw.attrs[f"plume{i}_region"]
            .split("(")[0]
            .lower()
            .strip()
            .replace(" ", "_")
            .encode()
            for i in range(1, 10)
        ],
        dtype=bytes,
    )
    ds_out["plume_region"] = xr.DataArray(
        data=regions,
        coords=(ds_out["plume_number"],),
        dims=("plume_number",),
    )

    # Set the time encoding
    ds_out["time"].encoding = {
        "calendar": "noleap",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    ds_out.attrs = {}

    # Fix up the attributes of the co-ordinates
    coord_attributes = {
        "plume_number": {"long_name": "plume number", "units": "1"},
        "plume_feature": {"long_name": "plume feature", "units": "1"},
        "time": {"standard_name": "time"},
        "year_fraction": {
            "long_name": "year fraction",
            "units": "years",
            "comment": "Required for calculating the seasonal cycle",
        },
    }
    for coord in ds_out.coords:
        ds_out.coords[coord].attrs = coord_attributes[coord]

    # I assume this is a mislabelling
    # [TODO: confirm and check which way around the relabelling should go]
    ds_out = ds_out.rename({"sig_lat_W": "sig_lat_N", "sig_lat_E": "sig_lat_S"})

    # Fix up the attributes of the variables
    variable_attributes = {
        "is_biomass": {
            "long_name": "Is the plume biomass dominated or not (1: yes, 0: no)",
            "units": "1",
        },
        "plume_lat": {
            "long_name": "Latitude of the plume's centre",
            "units": "degrees_north",
        },
        "sig_lat_N": {
            "long_name": (
                "Latitudinal extension of the feature north of its centre (unrotated)"
            ),
            "units": "degrees",
        },
        "sig_lat_S": {
            "long_name": (
                "Latitudinal extension of the feature south of its centre (unrotated)"
            ),
            "units": "degrees",
        },
        "plume_lon": {
            "long_name": "longitude of the plume's centre",
            "units": "degrees_east",
        },
        "sig_lon_E": {
            "long_name": (
                "Longitudinal extension of the feature east of its centre (unrotated)"
            ),
            "units": "degrees",
        },
        "sig_lon_W": {
            "long_name": (
                "Longitudinal extension of the feature west of its centre (unrotated)"
            ),
            "units": "degrees",
        },
        "theta": {
            "long_name": "Clockwise rotation of the feature's central axis",
            # [TODO Odd that this is in radians but everything else is in degrees?]
            "units": "radians",
        },
        "ftr_weight": {
            "long_name": "Feature weight",
            "units": "1",
        },
        "beta_a": {
            "long_name": (
                "Value of parameter `a` of the beta function "
                "which defines the vertical distribution"
            ),
            "units": "1",
        },
        "beta_b": {
            "long_name": (
                "Value of parameter `b` of the beta function "
                "which defines the vertical distribution"
            ),
            "units": "1",
        },
        "aod_fmbg": {
            "long_name": (
                "Background fine mode aerosol optical depth (AOD) at 550nm at source"
            ),
            "units": "1",
        },
        "aod_spmx": {
            "long_name": "Aerosol optical depth (AOD) at the source",
            "units": "1",
        },
        "ssa550": {
            "long_name": "Single scattering albedo at 550nm",
            "units": "1",
        },
        "asy550": {
            "long_name": "Asymmetry Factor at 550nm",
            "units": "1",
        },
        "angstrom": {
            "long_name": "Angstrom exponent",
            "units": "1",
        },
        "ann_cycle": {
            "long_name": "Annual cycle for each plume's features",
            "units": "1",
        },
        "year_weight": {
            "long_name": "Annual Scaling factor of plume amplitude",
            "units": "1",
        },
        "plume_region": {
            "long_name": "Plume's region",
        },
    }
    for var in ds_out.data_vars:
        ds_out[var].attrs = variable_attributes[var]

    ds_out = add_time_bounds(ds_out, yearly_time_bounds=True, monthly_time_bounds=False)
    ds_out = ds_out.cf.add_bounds("plume_number")
    ds_out = ds_out.cf.add_bounds("plume_feature")
    ds_out = ds_out.cf.add_bounds("year_fraction")

    # Hmmm, will need to roll my own function
    # to automatically do this removal from coordinates.
    # TODO: MR into cf-xarray?
    ds_out = ds_out.reset_coords(
        [
            "time_bounds",
            "plume_number_bounds",
            "plume_feature_bounds",
            "year_fraction_bounds",
        ]
    )

    # # This adds the wrong axis information for year_fraction
    # ds_out = ds_out.cf.guess_coord_axis()
    ds_out = ds_out.cf.add_canonical_attributes()

    # Ensure time comes first
    ds_out = ds_out.transpose("time", ...)

    ds_input4mips = Input4MIPsDataset(
        data=ds_out,
        cvs=cvs,
        metadata=input4mips_metadata,
        non_input4mips_metadata=non_input4mips_metadata,
    )

    out_path, ds_disk_ready = ds_input4mips.get_out_path_and_disk_ready_dataset(
        root_data_dir=output_dir,
    )

    # Validate
    validation_result = get_ds_to_write_to_disk_validation_result(
        ds=ds_disk_ready, out_path=out_path, cvs=cvs
    )
    validation_result.raise_if_errors()

    # Convert to cubes with ncdata
    cubes = ncdata.iris_xarray.cubes_from_xarray(ds_disk_ready)

    # Fix up some bugs from iris' conversion
    # [TODO: issue]
    for cube in cubes:
        va = variable_attributes[cube.var_name]
        try:
            units_specified = va["units"]

        except KeyError:
            # no unit info
            continue

        if str(cube.units) != units_specified:
            print(
                f"Iris mangled the units of {cube.var_name=}. "
                f"{units_specified=}. {cube.units=}."
                "Fixing now."
            )
            cube.units = units_specified

    # Having validated and converted to cubes, make the target directory.
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file to disk
    iris.save(
        cubes,
        out_path,
        unlimited_dimensions=("time",),
    )

    print(f"{out_path=}")

    get_validate_file_result(
        out_path,
        cvs=cvs,
    ).raise_if_errors()

    ds_written = xr.open_dataset(out_path)

    assert ds_written["plume_lat"].attrs["units"] == "degrees_north"
    assert ds_written["plume_lon"].attrs["units"] == "degrees_east"


if __name__ == "__main__":
    logger.enable("input4mips_validation")

    RAW_FILE = Path("MACv2.0-SP_v2.nc")
    OUTPUT_DIR = Path(".") / "macv2-rewrite"
    ORIGINAL_DATA_LINK = "url.to.somewhere"
    cvs = load_cvs(Path(__file__).parents[1] / ".." / "input4MIPs_CVs" / "CVs")

    input4mips_metadata = Input4MIPsDatasetMetadata(
        activity_id="input4MIPs",
        contact="sfiedler@geomar.de",
        dataset_category="aerosolProperties",
        frequency="yr",
        further_info_url="http://www.tbd.invalid",
        grid_label="gn",
        license=(
            "The input4MIPs data linked to this entry is licensed "
            "under a Creative Commons Attribution 4.0 International "
            "(https://creativecommons.org/licenses/by/4.0/). "
            "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
            "for terms of use governing CMIP6Plus output, "
            "including citation requirements and proper acknowledgment. "
            "The data producers and data providers make no warranty, either express "
            "or implied, including, but not limited to, warranties of merchantability "
            "and fitness for a particular purpose. "
            "All liabilities arising from the supply of the information "
            "(including any liability arising in negligence) "
            "are excluded to the fullest extent permitted by law."
        ),
        mip_era="CMIP6Plus",
        nominal_resolution="250 km",
        realm="atmos",
        # TODO: ask Stephanie whether switching or consortium or what
        institution_id="G-UHD",
        institution=None,
        source_id="G-UHD-SPv2-1-0",
        source_version="1.0",
        # source=None,
        target_mip="CMIP",
        variable_id="multiple-macv2sp",
        comment=(
            "This data has been re-written in the input4MIPs format. "
            "The data as required by the MACv2-SPv2 Fortran module "
            f"can be retrieved from {ORIGINAL_DATA_LINK}"
        ),
        doi=None,
        license_id="CC BY 4.0",
        # product=None,
        # region=None,
    )
    non_input4mips_metadata = {
        "references": "https://doi.org/10.5194/gmd-10-433-2017",
    }

    main(
        raw_file=RAW_FILE,
        output_dir=OUTPUT_DIR,
        cvs=cvs,
        input4mips_metadata=input4mips_metadata,
        non_input4mips_metadata=non_input4mips_metadata,
        # Only writing data out to the end of history right now
        years_to_keep=range(1850, 2020 + 1),
    )
