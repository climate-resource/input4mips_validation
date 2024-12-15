"""
This acts as a canary.

If these tests fail, lots of other things will likely go wrong.
"""

from __future__ import annotations

from input4mips_validation.testing import (
    get_valid_out_path_and_disk_ready_ds,
)
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
)


def test_valid_ds_passes(test_cvs):
    """
    Test that a valid dataset passes validation
    """
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    # Make sure that there are no errors
    get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    ).raise_if_errors()
