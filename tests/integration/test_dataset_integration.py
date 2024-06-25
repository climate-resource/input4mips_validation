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
import pytest
import xarray as xr
from attrs import asdict

from input4mips_validation.cvs_handling.exceptions import InconsistentWithCVsError
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

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (
        Path(__file__).parent / ".." / "test-data" / "cvs" / "input4MIPs" / "default"
    ).absolute()
)


def get_test_ds_metadata(
    ds_variable: str = "mole-fraction-of-carbon-dioxide-in-air",
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
    ds_data = rng.random((lon.size, lat.size, time.size))

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
        if k in ["activity_id"]
    }
    metadata_valid = {
        **metadata_valid_from_cvs,
        "source_id": valid_source_id_entry.source_id,
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


@pytest.mark.xfail(reason="write not implemented yet")
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

    # TODO: replace with cvs.get_file_path(**kwargs) or something
    exp_out_file = (
        tmp_path
        / metadata.activity_id
        / metadata.mip_era
        / metadata.target_mip
        / metadata.institution_id
        / metadata.source_id
        / metadata.realm
        / metadata.frequency
        / metadata.variable_id
        / metadata.grid_label
        / metadata.version
        / "_".join(
            [
                metadata.variable_id,
                metadata.activity_id,
                metadata.dataset_category,
                metadata.target_mip,
                metadata.source_id,
                metadata.grid_label,
                f"{metadata.time_range}.nc",
            ]
        )
    )

    assert out_file == exp_out_file


# TODO: write tests of
# - written file attributes
# - written file encoding
# - written file can be read using xarray and iris

# TODO: write test of pre-write checks in `write` e.g.
# - fails if no tracking_id
# - fails if no creation_date
# - fails if no time encoding


def test_from_data_producer_minimum_information():
    source_id = "CR-CMIP-0-2-0"

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        ds, _ = get_test_ds_metadata()

        exp = Input4MIPsDataset(
            ds=ds,
            metadata=Input4MIPsDatasetMetadata(
                activity_id="input4MIPs",
                source_id=source_id,
                variable_id=list(ds.data_vars)[0],  # noqa: RUF015
                metadata_non_cvs=None,
            ),
        )

        res = Input4MIPsDataset.from_data_producer_minimum_information(
            ds=ds,
            dimensions=(),
            time_dimension="time",
            metadata_minimum=Input4MIPsDatasetMetadataDataProducerMinimum(
                source_id=source_id
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


# TODO: Test of values that aren't in CV


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
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "institution_id",
        #     "Cr",
        # ),
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
