"""
Database validation
"""

from __future__ import annotations

import concurrent.futures

import tqdm
from attrs import evolve
from loguru import logger

from input4mips_validation.database.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.exceptions import NonUniqueError
from input4mips_validation.hashing import get_file_hash_sha256


def validate_database_file_entry(entry: Input4MIPsDatabaseEntryFile) -> None:
    # Check the sha to start
    sha256 = get_file_hash_sha256(entry.filepath)
    if sha256 != entry.sha256:
        msg = f"{entry.sha256=}, but we calculated a sha256 of {sha256} for {entry.filepath}"
        raise ValueError(msg)

    # validate_tree(
    #     entry.filepath,
    #     cvs=cvs,
    #     bnds_coord_indicator=bnds_coord_indicator,
    #     allow_cf_checker_warnings=allow_cf_checker_warnings,
    # )


def validate_database(
    db: tuple[Input4MIPsDatabaseEntryFile, ...],
    n_processes: int = 1,
) -> tuple[Input4MIPsDatabaseEntryFile, ...]:
    # If tracking IDs aren't unique, we can fail immediately
    tracking_ids = [e.tracking_id for e in db]
    if len(set(tracking_ids)) != len(db):
        raise NonUniqueError(
            description="Tracking IDs for all entries should be unique",
            values=tracking_ids,
        )

    entries_to_validate = [e for e in db if e.validated_input4mips is None]
    # Entries that can be passed straight through to the output
    out_l = [e for e in db if e.validated_input4mips is not None]

    logger.info(
        f"Validating {len(entries_to_validate)} database "
        f"{'entries' if len(entries_to_validate) > 1 else 'entry'} in parallel using "
        f"{n_processes} {'processes' if n_processes > 1 else 'process'}"
    )
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_processes) as executor:
        future_to_entry = {
            executor.submit(
                validate_database_file_entry,
                entry,
                # cvs=cvs,
                # frequency_metadata_key=frequency_metadata_key,
                # no_time_axis_frequency=no_time_axis_frequency,
                # time_dimension=time_dimension,
            ): entry
            for entry in tqdm.tqdm(
                entries_to_validate, desc="Submitting files to queue"
            )
        }

        for future in tqdm.tqdm(
            concurrent.futures.as_completed(future_to_entry),
            desc="Database file entries",
            total=len(future_to_entry),
        ):
            entry = future_to_entry[future]
            try:
                # Check if any error was raised
                future.result()
                out_l.append(evolve(entry, validated_input4mips=True))

            except Exception:
                logger.exception(f"Exception while validating {entry.filepath}")
                out_l.append(evolve(entry, validated_input4mips=False))

    return tuple(out_l)
