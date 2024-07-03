"""
Tests of dataset handling
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import pytest
import xarray as xr
from attrs import asdict

from input4mips_validation.cvs_handling.exceptions import (
    InconsistentWithCVsError,
    NotInCVsError,
)
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import (
    load_cvs,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadata,
    Input4MIPsDatasetMetadataDataProducerMinimum,
)
from input4mips_validation.exceptions import DatasetMetadataInconsistencyError

UR = pint.get_application_registry()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (
        Path(__file__).parent / ".." / "test-data" / "cvs" / "input4MIPs" / "default"
    ).absolute()
)


def get_test_ds_metadata(
    ds_variable: str = "mole_fraction_of_carbon_dioxide_in_air",
    ds_attrs: dict[str, Any] | None = None,
    metadata_overrides: dict[str, Any] | None = None,
) -> tuple[xr.Dataset, Input4MIPsDatasetMetadata]:
    if ds_attrs is None:
        ds_attrs = {}

    if metadata_overrides is None:
        metadata_overrides = {}

    lon = np.arange(-165, 180, 30)
    lat = np.arange(-82.5, 90, 15)
    time = pd.date_range("2000-01-01", periods=120, freq="MS")

    rng = np.random.default_rng()
    ds_data = UR.Quantity(
        rng.random((lon.size, lat.size, time.size)),
        "ppm",
    )

    ds = xr.Dataset(
        data_vars={
            ds_variable: (["lat", "lon", "time"], ds_data),
        },
        coords=dict(
            lon=("lon", lon),
            lat=("lat", lat),
            time=time,
        ),
        attrs=ds_attrs,
    )

    cvs_valid = load_cvs(get_raw_cvs_loader())
    valid_source_id_entry = cvs_valid.source_id_entries.entries[0]
    metadata_valid_from_cvs = {
        k: v
        for k, v in asdict(valid_source_id_entry.values).items()
        if k in ["activity_id", "mip_era", "institution_id", "version"]
    }
    metadata_valid = {
        **metadata_valid_from_cvs,
        "dataset_category": "GHGConcentrations",
        "frequency": "mon",
        "grid_label": "gn",
        "realm": "atmos",
        "source_id": valid_source_id_entry.source_id,
        "target_mip": "CMIP",
        "time_range": "-".join(
            [f"{t.year:04d}{t.month:02d}" for t in [time[0], time[-1]]]
        ),
        "variable_id": ds_variable,
    }
    metadata = Input4MIPsDatasetMetadata(**(metadata_valid | metadata_overrides))

    return ds, metadata


def test_valid_passes():
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, metadata = get_test_ds_metadata()
        # This should initialise without an issue
        Input4MIPsDataset(
            ds=ds,
            metadata=metadata,
        )


def test_ds_var_property():
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, metadata = get_test_ds_metadata()
        inst = Input4MIPsDataset(
            ds=ds,
            metadata=metadata,
        )

    res = inst.ds_var

    # Assert this is just a plain string, same as we'd get if we look at metadata
    # (which is same as what is in the data because metadata and data are
    # checked as being consistent at initialisation time)
    assert res == metadata.variable_id


def test_ds_more_than_one_var_error():
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, metadata = get_test_ds_metadata()

        # Add a second variable to the dataset
        first_variable_name = list(ds.data_vars)[0]  # noqa: RUF015
        second = (
            ds.data_vars[first_variable_name]
            .copy()
            .rename(f"{first_variable_name}_extra")
        )

        ds = ds.merge(second)

        error_msg = "The value used for `ds` must only contain a single variable"
        with pytest.raises(AssertionError, match=error_msg):
            Input4MIPsDataset(
                ds=ds,
                metadata=metadata,
            )


def test_valid_writing_path(tmp_path):
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, metadata = get_test_ds_metadata()

        input4mips_ds = Input4MIPsDataset(
            ds=ds,
            metadata=metadata,
        )

        out_file = input4mips_ds.write(root_data_dir=tmp_path)

        cvs = load_cvs(get_raw_cvs_loader())

    exp_out_file = tmp_path / cvs.get_file_path(metadata)

    assert out_file == exp_out_file


def test_from_data_producer_minimum_information():
    source_id = "CR-CMIP-0-2-0"

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, exp_metadata = get_test_ds_metadata()

        exp = Input4MIPsDataset(
            ds=ds,
            metadata=exp_metadata,
        )

        res = Input4MIPsDataset.from_data_producer_minimum_information(
            ds=ds,
            metadata_minimum=Input4MIPsDatasetMetadataDataProducerMinimum(
                grid_label="gn", source_id=source_id, target_mip="CMIP"
            ),
        )

    assert exp == res


def test_ds_variable_metadata_variable_mismatch_error():
    variable_ds = "co2"
    variable_metadata = "mole-fraction-of-carbon-dioxide-in-air"

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, metadata = get_test_ds_metadata(
            ds_variable=variable_ds,
            metadata_overrides=dict(variable_id=variable_metadata),
        )

        error_msg = re.escape(
            "The dataset's variable must match metadata.variable_id. "
            f"dataset_variable={variable_ds!r}, {metadata.variable_id=!r}"
        )
        with pytest.raises(DatasetMetadataInconsistencyError, match=error_msg):
            Input4MIPsDataset(ds=ds, metadata=metadata)


@pytest.mark.parametrize(
    "cv_source, key_to_test, value_to_apply",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "activity_id",
            "junk",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "source_id",
            "junk",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "institution_id",
            "junk",
        ),
        # License logic is much more complicated and depends on other things
        # so maybe don't include here
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "license",
        #     "license text",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "mip_era",
        #     "junk",
        # ),
    ),
)
def test_value_not_in_cv(cv_source, key_to_test, value_to_apply):
    """
    Test that an error is raised if we use a value that is not in the CVs
    """
    with patch.dict(os.environ, {"INPUT4MIPS_VALIDATION_CV_SOURCE": cv_source}):
        ds, metadata = get_test_ds_metadata(
            metadata_overrides={key_to_test: value_to_apply}
        )

        error_msg = (
            f"Received {key_to_test}={value_to_apply!r}. "
            "This is not in the available CV values:.*"
            + re.escape(f"CVs raw data loaded with: {get_raw_cvs_loader()}. ")
        )
        with pytest.raises(NotInCVsError, match=error_msg):
            Input4MIPsDataset(ds=ds, metadata=metadata)


@pytest.mark.parametrize(
    "cv_source, source_id, key_to_test, value_to_apply",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "activity_id",
            "CMIP",
        ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "contact",
        #     "zeb@cr.com",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "further_info_url",
        #     "http://www.tbd.com/elsewhere",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "institution",
        #     "CR name here",
        # ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "institution_id",
            "PCMDI",
        ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "license",
        #     "license text",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "mip_era",
        #     "CMIP7",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "version",
        #     "0.2.1",
        # ),
    ),
)
def test_value_conflict_with_source_id_inferred_value(
    cv_source, source_id, key_to_test, value_to_apply
):
    """
    Test that an error is raised if we use a value
    that is inconsistent with the value we can infer from the source_id and the CV
    """
    with patch.dict(os.environ, {"INPUT4MIPS_VALIDATION_CV_SOURCE": cv_source}):
        _, metadata_valid = get_test_ds_metadata()
        value_according_to_cv = getattr(metadata_valid, key_to_test)
        if value_according_to_cv == value_to_apply:
            msg = (
                "The test won't work if the CV's value "
                "and the applied value are the same"
            )
            raise AssertionError(msg)

        ds, metadata = get_test_ds_metadata(
            metadata_overrides={key_to_test: value_to_apply}
        )

        error_msg = re.escape(
            f"For source_id={source_id!r}, "
            f"we should have {key_to_test}={value_according_to_cv!r}. "
            f"Received {key_to_test}={value_to_apply!r}. "
            f"CVs raw data loaded with: {get_raw_cvs_loader()}. "
        )
        with pytest.raises(InconsistentWithCVsError, match=error_msg):
            Input4MIPsDataset(ds=ds, metadata=metadata)
