# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.

<!--
You should *NOT* be adding new changelog entries to this file,
this file is managed by towncrier.
See `changelog/README.md`.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
`changelog/README.md`
and https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news,
markdown instead of restructured text and use slightly different categories
from the examples given in that link.
-->

<!-- towncrier release notes start -->

## Input4MIPs validation v0.19.1 (2025-02-08)


### 🎉 Improvements

- Added the ability to handle data sets with string variables, like region.
  The key logic improvement is in [`XRVariableProcessorLike.get_ds_variables`][input4mips_validation.xarray_helpers.variables.XRVariableProcessorLike.get_ds_variables], which now excludes any non-number variables from the dataset's variables. ([#113](https://github.com/climate-resource/input4mips_validation/pull/113))


## Input4MIPs validation v0.19.0 (2024-12-26)


### ⚠️ Breaking Changes

- Removed `input4mips_validation.database.creation.create_db_file_entry_with_logging`, this function was never meant to be released. ([#111](https://github.com/climate-resource/input4mips_validation/pull/111))


## Input4MIPs validation v0.18.0 (2024-12-23)


### ⚠️ Breaking Changes

- Changed the interface to `input4mips_validation.database.creation.create_db_file_entry_with_logging`.
  Both of these functions were intended for internal use, hence this should hopefully cause minor issues for users. ([#106](https://github.com/climate-resource/input4mips_validation/pull/106))
- Removed (the mostly internal interfaces) `input4mips_validation.logging_config.serialise_logging_config` and `input4mips_validation.logging_config.deserialise_logging_config`.
  We don't think these are in general need, although it is still being figured out (see [#108](https://github.com/climate-resource/input4mips_validation/issues/108)). ([#107](https://github.com/climate-resource/input4mips_validation/pull/107))

### 🆕 Features

- Added the `--mp-context-id` option to the command-line interfaces that support multiprocessing to give the user more control of how the multiprocessing is done.
  This is then passed down the stack to [`input4mips_validation.parallelisation.run_parallel`][input4mips_validation.parallelisation.run_parallel]. ([#107](https://github.com/climate-resource/input4mips_validation/pull/107))

### 🎉 Improvements

- Added [`input4mips_validation.parallelisation`][input4mips_validation.parallelisation] to assist with simplifying parallelisation, mainly for internal use. ([#106](https://github.com/climate-resource/input4mips_validation/pull/106))
- Added `xr_load_kwargs` to [`input4mips_validation.xarray_helpers.iris.ds_from_iris_cubes`][input4mips_validation.xarray_helpers.iris.ds_from_iris_cubes].
  By default, this sets things up so the user doesn't get a thousand warnings about using cftime rather than numpy time objects
  (but the user can pass the argument to change this however they wish). ([#107](https://github.com/climate-resource/input4mips_validation/pull/107))


## Input4MIPs validation v0.17.1 (2024-12-22)


### 🐛 Bug Fixes

- Fixed up addition of bounds when using climatology data (time bounds are no longer added). ([#104](https://github.com/climate-resource/input4mips_validation/pull/104))


## Input4MIPs validation v0.17.0 (2024-12-22)


### ⚠️ Breaking Changes

- - `input4mips_validation.inference.from_data.infer_time_start_time_end` renamed to [`input4mips_validation.inference.from_data.infer_time_start_time_end_for_filename`][input4mips_validation.inference.from_data.infer_time_start_time_end_for_filename].
  - `input4mips_validation.inference.from_data.create_time_range` renamed to [`input4mips_validation.inference.from_data.create_time_range_for_filename`][input4mips_validation.inference.from_data.create_time_range_for_filename].

  ([#103](https://github.com/climate-resource/input4mips_validation/pull/103))

### 🆕 Features

- Added [`input4mips_validation.validation.external_variables.validate_external_variables`][input4mips_validation.validation.external_variables.validate_external_variables]. ([#98](https://github.com/climate-resource/input4mips_validation/pull/98))
- Added [`input4mips_validation.validation.frequency.validate_frequency`][input4mips_validation.validation.frequency.validate_frequency]. ([#100](https://github.com/climate-resource/input4mips_validation/pull/100))
- Added support for data that represents a monthly climatology. ([#103](https://github.com/climate-resource/input4mips_validation/pull/103))

### 🎉 Improvements

- Split [`input4mips_validation.validation.allowed_characters`][input4mips_validation.validation.allowed_characters] into its own module. ([#98](https://github.com/climate-resource/input4mips_validation/pull/98))
- Added [`input4mips_validation.inference.from_data.BoundsInfo`][input4mips_validation.inference.from_data.BoundsInfo] and propagated it throughout the stack, to make it easier to specify how the bounds variables should be handled. ([#100](https://github.com/climate-resource/input4mips_validation/pull/100))

### 🐛 Bug Fixes

- Fixed the behaviour of [`input4mips_validation.cvs.loading_raw.get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader]
  (and therefore [`input4mips_validation.cvs.loading.load_cvs`][input4mips_validation.cvs.loading.load_cvs])
  when the `INPUT4MIPS_VALIDATION_CV_SOURCE_FORCE_DOWNLOAD` environment variable was set. ([#101](https://github.com/climate-resource/input4mips_validation/pull/101))

### 🔧 Trivial/Internal Changes

- [#103](https://github.com/climate-resource/input4mips_validation/pull/103)


## Input4MIPs validation v0.16.0 (2024-12-16)


### ⚠️ Breaking Changes

- Renamed `bnds_coord_indicator` to `bnds_coord_indicators` throughout.
  This breaks the API, albeit it is a rarely used part of the API
  and the defaults are sensible.
  Wherever `bnds_coord_indicator` was used, it now needs to be replaced with a set of strings, e.g. `{"bnds"}`.
  If using the command-line option, then `--bnds-coord-indicator 'bnds'`
  would be replaced with `--bnds-coord-indicators 'bnds'`
  and there is now also the possibility to provide multiple values
  with e.g. `--bnds-coord-indicators 'bnds;bounds'`. ([#87](https://github.com/climate-resource/input4mips_validation/pull/87))
- - Removed `validate_database_file_entry`, `validate_ds_to_write_to_disk`, `validate_file` and `validate_tree` following scheduled deprecation. ([#88](https://github.com/climate-resource/input4mips_validation/pull/88))
- Simplified the API in many places.
  This was an attempt to group things which are passed through
  and to make the injectable behaviour clearer throughout.
  Specific changes:

  - Interfaces that now take a [`FrequencyMetadataKeys`][input4mips_validation.inference.from_data.FrequencyMetadataKeys] rather than `frequency_metadata_key` and `no_time_axis_frequency`:
      - [`DataReferenceSyntax.validate_file_written_according_to_drs`][input4mips_validation.cvs.drs.DataReferenceSyntax.validate_file_written_according_to_drs]
      - [`Input4MIPsDatabaseEntryFile.from_file`][input4mips_validation.database.database.Input4MIPsDatabaseEntryFile.from_file]
      - [`create_db_file_entries`][input4mips_validation.database.creation.create_db_file_entries]
      - [`get_validate_database_file_entry_result`][input4mips_validation.validation.database.get_validate_database_file_entry_result]
  - Interfaces that now take a [`XRVariableProcessorLike`][input4mips_validation.xarray_helpers.variables.XRVariableProcessorLike] rather than `bnds_coord_indicators`:
      - [`Input4MIPsDataset.write`][input4mips_validation.dataset.dataset.Input4MIPsDataset.write]
      - [`ds_from_iris_cubes`][input4mips_validation.xarray_helpers.iris.ds_from_iris_cubes]
      - [`get_ds_to_write_to_disk_validation_result`][input4mips_validation.validation.datasets_to_write_to_disk.get_ds_to_write_to_disk_validation_result]
      - [`get_validate_file_result`][input4mips_validation.validation.file.get_validate_file_result]
  - Interfaces that now take both a [`FrequencyMetadataKeys`][input4mips_validation.inference.from_data.FrequencyMetadataKeys] rather than `frequency_metadata_key` and `no_time_axis_frequency` and a [`XRVariableProcessorLike`][input4mips_validation.xarray_helpers.variables.XRVariableProcessorLike] rather than `bnds_coord_indicators`:
      - [`get_validate_tree_result`][input4mips_validation.validation.tree.get_validate_tree_result]
      - [`validate_database_entries`][input4mips_validation.validation.database.validate_database_entries]

  ([#89](https://github.com/climate-resource/input4mips_validation/pull/89))

### 🆕 Features

- Added v6.6.0 of the input4MIPs CVs as a known CV source. ([#84](https://github.com/climate-resource/input4mips_validation/pull/84))
- Added [`input4mips_validation.testing.get_valid_out_path_and_disk_ready_ds`][input4mips_validation.testing.get_valid_out_path_and_disk_ready_ds]. ([#85](https://github.com/climate-resource/input4mips_validation/pull/85))
- Added the [`xarray_helpers.variables`][input4mips_validation.xarray_helpers.variables] module
  to help with extracting the variables from an xarray object. ([#87](https://github.com/climate-resource/input4mips_validation/pull/87))
- - Added [`FrequencyMetadataKeys`][input4mips_validation.inference.from_data.FrequencyMetadataKeys]
  - Added [`XRVariableHelper`][input4mips_validation.xarray_helpers.variables.XRVariableHelper]

  ([#89](https://github.com/climate-resource/input4mips_validation/pull/89))
- Added Python-equivalent APIs for our CLI commands, see
  [`validate_file`][`input4mips_validation.cli.validate_file`],
  [`validate_tree`][`input4mips_validation.cli.validate_tree`],
  [`db_create`][`input4mips_validation.cli.db.db_create`],
  [`db_add_tree`][`input4mips_validation.cli.db.db_add_tree`]
  and [`db_validate`][`input4mips_validation.cli.db.db_validate`]. ([#90](https://github.com/climate-resource/input4mips_validation/pull/90))
- Added validation of the "Conventions" attribute via [`input4mips_validation.validation.Conventions`][input4mips_validation.validation.Conventions] ([#91](https://github.com/climate-resource/input4mips_validation/pull/91))
- Added [`input4mips_validation.cvs.Input4MIPsCVs.validate_activity_id`][input4mips_validation.cvs.Input4MIPsCVs.validate_activity_id] and [`input4mips_validation.cvs.exceptions`][input4mips_validation.cvs.exceptions]. ([#92](https://github.com/climate-resource/input4mips_validation/pull/92))
- Added [`input4mips_validation.cvs.Input4MIPsCVs.validate_source_version`][input4mips_validation.cvs.Input4MIPsCVs.validate_source_version] and [`input4mips_validation.cvs.exceptions.ValueInconsistentWithCVsError`][input4mips_validation.cvs.exceptions.ValueInconsistentWithCVsError]. ([#93](https://github.com/climate-resource/input4mips_validation/pull/93))
- Added [`input4mips_validation.cvs.Input4MIPsCVs.validate_contact`][input4mips_validation.cvs.Input4MIPsCVs.validate_contact]. ([#94](https://github.com/climate-resource/input4mips_validation/pull/94))
- Added [`input4mips_validation.validation.comment.validate_comment`][input4mips_validation.validation.comment.validate_comment]. ([#95](https://github.com/climate-resource/input4mips_validation/pull/95))

### 🎉 Improvements

- Added headers to the default pooch downloader to workaround https://github.com/readthedocs/readthedocs.org/issues/11763.
  The downloader is injectable, so this behaviour can be overridden if desired. ([#84](https://github.com/climate-resource/input4mips_validation/pull/84))
- If a required attribute is missing during validation, we now raise the more explicit [`MissingAttributeError`][input4mips_validation.validation.exceptions.MissingAttributeError], rather than a `KeyError`. ([#86](https://github.com/climate-resource/input4mips_validation/pull/86))

### 📚 Improved Documentation

- Updated the docs to use v6.6.0 of the CVs rather than a specific SHA. ([#84](https://github.com/climate-resource/input4mips_validation/pull/84))

### 🔧 Trivial/Internal Changes

- [#84](https://github.com/climate-resource/input4mips_validation/pull/84), [#85](https://github.com/climate-resource/input4mips_validation/pull/85), [#86](https://github.com/climate-resource/input4mips_validation/pull/86), [#87](https://github.com/climate-resource/input4mips_validation/pull/87), [#89](https://github.com/climate-resource/input4mips_validation/pull/89), [#92](https://github.com/climate-resource/input4mips_validation/pull/92)


## Input4MIPs validation v0.15.0 (2024-11-11)


### ⚠️ Breaking Changes

- Updated to better be in line with [the DRS description](https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk).
  The DRS makes no comment on the values in the directory names,
  hence we now make no assumptions and put no requirements on characters used in directory names.
  The restriction to only a-z, A-Z, 0-9 and the hyphen plus special use of the underscore
  is now only applied to file names.
  As a result, files with variables that have underscores in their names
  are now written with underscores in their directories, but not in their file name.
  For example,
  `.../mon/mole-fraction-of-methane-in-air/gn/.../mole-fraction-of-methane-in-air_input4MIPs_GHGConcentrations_CMIP_CR-CMIP-0-2-0_gn_200001-201012.nc`
  is now written as
  `.../mon/mole_fraction_of_methane_in_air/gn/.../mole-fraction-of-methane-in-air_input4MIPs_GHGConcentrations_CMIP_CR-CMIP-0-2-0_gn_200001-201012.nc`. ([#83](https://github.com/climate-resource/input4mips_validation/pull/83))

### 🐛 Bug Fixes

- Fixed a bug in
  [`validate_file_written_according_to_drs`][input4mips_validation.cvs.drs.DataReferenceSyntax.validate_file_written_according_to_drs]
  which caused it to break if the file contained metadata which was not a string. ([#83](https://github.com/climate-resource/input4mips_validation/pull/83))

### 🔧 Trivial/Internal Changes

- [#81](https://github.com/climate-resource/input4mips_validation/pull/81), [#83](https://github.com/climate-resource/input4mips_validation/pull/83)


## Input4MIPs validation v0.14.0 (2024-11-05)


### ⚠️ Breaking Changes

- - The function signatures for [`input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information`][]
    and [`input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable`][]
    have now been simplified to use an injectable [`prepare_func`][`input4mips_validation.dataset.dataset.PrepareFuncLike`][],
    the default value of which is [`input4mips_validation.dataset.dataset.prepare_ds_and_get_frequency`][].
    This makes the API simpler and gives the user more control.
    However, it is a breaking change.
  - We removed fine-grained control of writing to disk when using [`Input4MIPsDataset.write`][input4mips_validation.dataset.Input4MIPsDataset.write]
    and [`input4mips_validation.io.write_ds_to_disk`][].
    Instead, use [`Input4MIPsDataset.get_out_path_and_disk_ready_dataset`][input4mips_validation.dataset.Input4MIPsDataset.get_out_path_and_disk_ready_dataset]
    or [`input4mips_validation.io.prepare_out_path_and_cubes`][] then write using you own writing function
    (typically [`iris.save`][] instead).
  - Renamed `bounds_dim` to `bounds_indicator` in [`input4mips_validation.dataset.dataset.handle_ds_standard_long_names`][].

  ([#80](https://github.com/climate-resource/input4mips_validation/pull/80))

### 🆕 Features

- - Added [`Input4MIPsDataset.get_out_path_and_disk_ready_dataset`][input4mips_validation.dataset.Input4MIPsDataset.get_out_path_and_disk_ready_dataset]
    and [`input4mips_validation.io.prepare_out_path_and_cubes`][]
    to permit finer-grained control of file preparation and writing.
  - Added [`input4mips_validation.dataset.dataset.add_bounds`][].

  ([#80](https://github.com/climate-resource/input4mips_validation/pull/80))

### 🐛 Bug Fixes

- Fixed up passing of input arguments to underlying functions in `input4mips-validation validate-tree` ([#75](https://github.com/climate-resource/input4mips_validation/pull/75))
- [`input4mips_validation.cvs.load_cvs`][] now supports variables of type `Path` for the `cv_source` argument.
  As part of this fix, [`input4mips_validation.cvs.loading_raw.get_raw_cvs_loader`][] now also supports variables of type `Path` for the `cv_source` argument. ([#80](https://github.com/climate-resource/input4mips_validation/pull/80))

### 🔧 Trivial/Internal Changes

- [#79](https://github.com/climate-resource/input4mips_validation/pull/79)


## Input4MIPs validation v0.13.2 (2024-10-16)


### 🎉 Improvements

- Improved the error message if regexp parsing of paths fails for a given DRS. ([#74](https://github.com/climate-resource/input4mips_validation/pull/74))

### 🔧 Trivial/Internal Changes

- [#72](https://github.com/climate-resource/input4mips_validation/pull/72)


## Input4MIPs validation v0.13.0 (2024-09-30)


### 🆕 Features

- Add `--continue-on-error` flag to `input4mips-validation upload-ftp` ([#69](https://github.com/climate-resource/input4mips_validation/pull/69))
- Added validation of the tracking_id attribute, see [`input4mips_validation.validation.tracking_id.validate_tracking_id`][]. ([#70](https://github.com/climate-resource/input4mips_validation/pull/70))

### 🐛 Bug Fixes

- Fixed total failure of validation if an expected attribute wasn't in the file being validated. ([#70](https://github.com/climate-resource/input4mips_validation/pull/70))

### 🔧 Trivial/Internal Changes

- [#67](https://github.com/climate-resource/input4mips_validation/pull/67), [#68](https://github.com/climate-resource/input4mips_validation/pull/68), [#69](https://github.com/climate-resource/input4mips_validation/pull/69), [#71](https://github.com/climate-resource/input4mips_validation/pull/71)


## Input4MIPs validation v0.12.0 (2024-08-29)


### 🗑️ Deprecations

- Deprecated [`validate_database_file_entry`], [`validate_ds_to_write_to_disk`], [`validate_file`] and [`validate_tree`].
  See the docs for each function and deprecation warnings for recommended alternatives. ([#66](https://github.com/climate-resource/input4mips_validation/pull/66))

### 🆕 Features

- Added the `--output-html` flag to `input4mips-validation validate-tree`.
  This allows you to output the results of the validation as HTML,
  which provides easier exploration of the failures. ([#66](https://github.com/climate-resource/input4mips_validation/pull/66))

### 📚 Improved Documentation

- Improved documentation of our command-line interface,
  particularly how to configure logging. ([#65](https://github.com/climate-resource/input4mips_validation/pull/65))

### 🔧 Trivial/Internal Changes

- [#65](https://github.com/climate-resource/input4mips_validation/pull/65)


## Input4MIPs validation v0.11.4 (2024-08-23)


### 🆕 Features

- Add "doi" to the list of fields tracked by our database entries. ([#64](https://github.com/climate-resource/input4mips_validation/pull/64))

### 🔧 Trivial/Internal Changes

- [#62](https://github.com/climate-resource/input4mips_validation/pull/62)


## Input4MIPs validation v0.11.3 (2024-08-06)


### 🎉 Improvements

- Made it explicit that [cftime](https://unidata.github.io/cftime/) and [typing-extensions](https://typing-extensions.readthedocs.io/en/latest/#) are required ([#59](https://github.com/climate-resource/input4mips_validation/pull/59))

### 🐛 Bug Fixes

- Fixed up the writing of the `creation_time` attribute and datetime metadata inference to use the expected time format ([#60](https://github.com/climate-resource/input4mips_validation/pull/60))

### 🔧 Trivial/Internal Changes

- [#60](https://github.com/climate-resource/input4mips_validation/pull/60)


## Input4MIPs validation v0.11.2 (2024-08-05)


### 🔧 Trivial/Internal Changes

- [#57](https://github.com/climate-resource/input4mips_validation/pull/57)


## Input4MIPs validation v0.11.1 (2024-08-03)

### 🎉 Improvements

- Added support for data without a time axis to
  [`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information]
  and [`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable]. ([#56](https://github.com/climate-resource/input4mips_validation/pull/56))

### 🐛 Bug Fixes

- Fixed the type hint for `datetime_end`, `datetime_start` and `time_range`.
  These fields will now serialise and de-serialise correctly.
  Previously, if these fields were `None`, they were serialised and de-serialised as strings. ([#56](https://github.com/climate-resource/input4mips_validation/pull/56))

### 🔧 Trivial/Internal Changes

- [#56](https://github.com/climate-resource/input4mips_validation/pull/56)


## Input4MIPs validation v0.11.0 (2024-08-02)


### ⚠️ Breaking Changes

- - Removed the `--create-db-entry` flag from the `validate-file` command.
    Use the newly added `input4mips-validation db` commands to control the database instead.
  - Our databases our now multi-file, one file per file entry. This makes it much easier to track changes to the database.
    To load a database from a directory of files, use [`load_database_file_entries`][input4mips_validation.database.database.load_database_file_entries]
  - Changed the function signature of [`input4mips_validation.cvs.loading.load_cvs`][input4mips_validation.cvs.loading.load_cvs].
    Now it simply expects the `cv_source` rather than requiring a [`RawCVLoader`][input4mips_validation.cvs.loading_raw.RawCVLoader] as input.

  ([#55](https://github.com/climate-resource/input4mips_validation/pull/55))

### 🆕 Features

- Added the ` --allow-cf-checker-warnings` flag to the `validate-file` and `validate-tree` commands.
  This allows the validation to pass, even if the CF-checker raises a warning.
  This was added because the CF-checker's warnings are sometimes overly strict. ([#52](https://github.com/climate-resource/input4mips_validation/pull/52))
- - Added `input4mips-validation db` command group for handling database creation and manipulation.
    This includes:

    - `input4mips-validation db create` for creating new databases
    - `input4mips-validation db add-tree` for adding files from a tree to an existing databases
    - `input4mips-validation db validate` for updating the validation status of the entries in a database

  - Added [`input4mips_validation.validation.database`][input4mips_validation.validation.database] for database validation

  - Added [`input4mips_validation.logging_config`][input4mips_validation.logging_config]
    to support passing of logging configuration between parallel processes.
    We're not sure if this is a great solution.
    If you have another solution, PRs welcome!

  ([#55](https://github.com/climate-resource/input4mips_validation/pull/55))

### 🎉 Improvements

- - Updated the type and default value of
    [`Input4MIPsDatabaseEntryFile.validated_input4mips`][input4mips_validation.database.Input4MIPsDatabaseEntryFile.validated_input4mips]
    to clarify the different states of validation.
  - Parallelised [`create_db_file_entries`][input4mips_validation.database.creation.create_db_file_entries]

  ([#55](https://github.com/climate-resource/input4mips_validation/pull/55))

### 🐛 Bug Fixes

- Fixed a missing f-string marker in `validate-tree`'s logging. ([#52](https://github.com/climate-resource/input4mips_validation/pull/52))
- - Set `use_cftime=True` whenever we call `xr.open_dataset` to avoid spurious warnings
  - Only pass the directory to `extract_metadata_from_path` in [`DRS.validate_file_written_according_to_drs`][input4mips_validation.cvs.drs.DataReferenceSyntax.validate_file_written_according_to_drs].
    This helps reduce the chance of incorrecetly parsing the metadata.

  ([#55](https://github.com/climate-resource/input4mips_validation/pull/55))

### 📚 Improved Documentation

- Clarified the meaning of the `timestamp` and `version` fields in our database entries ([#54](https://github.com/climate-resource/input4mips_validation/pull/54))
- Added documentation for how to manage a database ([#55](https://github.com/climate-resource/input4mips_validation/pull/55))

### 🔧 Trivial/Internal Changes

- [#55](https://github.com/climate-resource/input4mips_validation/pull/55)


## Input4MIPs validation v0.10.2 (2024-07-28)


### 🐛 Bug Fixes

- Make [loguru-config](https://github.com/erezinman/loguru-config) an optional dependency in `pyproject.toml` too ([#50](https://github.com/climate-resource/input4mips_validation/pull/50))

### 🔧 Trivial/Internal Changes

- [#50](https://github.com/climate-resource/input4mips_validation/pull/50)


## Input4MIPs validation v0.10.1 (2024-07-28)


### 🎉 Improvements

- Clarify handling of dry run in [`upload_ftp`][input4mips_validation.upload_ftp] ([#45](https://github.com/climate-resource/input4mips_validation/pull/45))
- [loguru-config](https://github.com/erezinman/loguru-config)
  is now an optional dependency.
  This makes it possible to install the package from conda
  without things exploding, as loguru-config is not available on conda.
  This may be changed in future, if loguru-config is released on conda
  (relevant MR here: https://github.com/conda-forge/staged-recipes/pull/27110) ([#48](https://github.com/climate-resource/input4mips_validation/pull/48))

### 🔧 Trivial/Internal Changes

- [#44](https://github.com/climate-resource/input4mips_validation/pull/44), [#46](https://github.com/climate-resource/input4mips_validation/pull/46), [#47](https://github.com/climate-resource/input4mips_validation/pull/47), [#49](https://github.com/climate-resource/input4mips_validation/pull/49)


## Input4MIPs validation v0.10.0 (2024-07-27)


### ⚠️ Breaking Changes

- - Removed `--verbose` option from the `input4mips-validation` command
  - Moved logging to `input4mips_validation.logging`

  ([#40](https://github.com/climate-resource/input4mips_validation/pull/40))

### 🆕 Features

- - Added `--version` flag to the `input4mips-validation` command

  - Added `--no-logging` to the `input4mips-validation` command to disable logging
  - Added `--logging-config` to the `input4mips-validation` command to allow the user to specify the path to the logging configuration file
  - Added `--logging-level` to the `input4mips-validation` command to allow the user to simply specify the logging level to use. Note that `--logging-config` takes precedence over this flag.

  - Fixed up the logging levels throughout the CLI and associated commands

  - Added the [`Input4MIPsDataset.non_input4mips_metadata`][input4mips_validation.dataset.Input4MIPsDataset.non_input4mips_metadata]
    attribute to handle metadata that is not part of the known input4MIPs keys
  - Added [`Input4MIPsDataset.from_ds`][input4mips_validation.dataset.Input4MIPsDataset.from_ds]
    to allow easy creation from a loaded [xarray.Dataset][]

  - Added the `--rglob-input` option to better control files of interest.
    This appplies to both `input4mips-validation validate-tree`
    and `input4mips-validation create-db`

  - Added [`input4mips_validation.hashing`][input4mips_validation.hashing]

  - Added [`DataReferenceSyntax.get_esgf_dataset_master_id`][input4mips_validation.cvs.drs.DataReferenceSyntax.get_esgf_dataset_master_id]

  ([#40](https://github.com/climate-resource/input4mips_validation/pull/40))
- - Added the `input4mips-validation upload-ftp` command
  - Added [`input4mips_validation.upload_ftp`][input4mips_validation.upload_ftp]

  ([#43](https://github.com/climate-resource/input4mips_validation/pull/43))

### 🎉 Improvements

- - Added support for fields used by input4MIPs database:
      - comment
      - comment_post_publication
      - data_node
      - esgf_dataset_master_id
      - filepath
      - latest
      - publication_status
      - replica
      - sha256
      - timestamp
      - validated_input4mips
      - xlink

  - Made all metadata-related classes frozen so they can be hashed,
    which makes sorting and comparison easier
    (and has almost no downsides
    as these classes do not generally need to be changed once created,
    and if they do need to be changed, that can be done with [attrs.evolve][]).

  - Made [commit `52841b0117474efd2705a083c21b3760531974f3`](https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/52841b0117474efd2705a083c21b3760531974f3/CVs/)
    a known registry for the raw CVs.

  ([#40](https://github.com/climate-resource/input4mips_validation/pull/40))

### 🐛 Bug Fixes

- - Fixed a bug in the behaviour of `input4mips-validation validate-file`'s `--write-in-drs` flag.
    If this flag is used, this command now fixes file names too
    and will update the tracking ID and creation ID
    if anything about the file (including its name) is changed.
    The command now also raises an error if you try overwrite an existing file.
  - Removed the product and region properties from the minimum dataset producer metadata related classes
  - Replaced all uses of [xarray.load_dataset][] with [xarray.open_dataset][].
    The latter doesn't load the file's data into memory, hence is much faster
    (especially for large files).
  - Fixed the behaviour of [`Input4MIPsDatabaseEntryFile.from_file`][input4mips_validation.database.database.Input4MIPsDatabaseEntryFile.from_file].
    Now, if there is a clash between metadata, a warning is logged
    but the existing value is used
    (i.e. the value from higher-priority sources is used)
    rather than an error being raised.

  ([#40](https://github.com/climate-resource/input4mips_validation/pull/40))

### 📚 Improved Documentation

- Updated README so that the snippet comments don't show up ([#37](https://github.com/climate-resource/input4mips_validation/pull/37))
- - Added docs about project status to the README
  - Added docs about preparing a file in the how-to guides. How to upload will come in the next MR.
      - See ["How can I prepare my input4MIPs files for publication on ESGF?"](https://input4mips-validation.readthedocs.io/en/latest/how-to-guides/#how-can-i-prepare-my-input4mips-files-for-publication-on-esgf)

  ([#40](https://github.com/climate-resource/input4mips_validation/pull/40))
- Added documentation about how to upload to an FTP server, and cross-linked these with the rest of the docs ([#43](https://github.com/climate-resource/input4mips_validation/pull/43))

### 🔧 Trivial/Internal Changes

- [#40](https://github.com/climate-resource/input4mips_validation/pull/40)


## Input4MIPs validation v0.9.0 (2024-07-24)


### 🆕 Features

- Added the `validate-tree` and `create-db` commands.

  These allow you to validate a tree of files
  and create a database of the files in the tree.

  Use the following commands to get help:

  - `input4mips-validation validate-tree --help`
  - `input4mips-validation create-db --help`

  ([#36](https://github.com/climate-resource/input4mips_validation/pull/36))

### 📚 Improved Documentation

- - Updated the installation instructions now that we have a
    [conda package](https://anaconda.org/conda-forge/input4mips-validation).
  - Generally cleaned up the docs

  ([#36](https://github.com/climate-resource/input4mips_validation/pull/36))

### 🔧 Trivial/Internal Changes

- [#36](https://github.com/climate-resource/input4mips_validation/pull/36)


## Input4MIPs validation v0.8.1 (2024-07-22)


### 🔧 Trivial/Internal Changes

- [#34](https://github.com/climate-resource/input4mips_validation/pull/34)


## Input4MIPs validation v0.8.0 (2024-07-22)


### ⚠️ Breaking Changes

- Completely re-wrote the package.

  The APIs are similar, but not identical.
  Given there are no users, we don't provide a migration guide.

  Key changes:

  - cleaned up the API to make clearer the different elements
  - changed dev tooling to supporting conda packages, because we needed iris

  ([#31](https://github.com/climate-resource/input4mips_validation/pull/31))

### 📚 Improved Documentation

- Updated README badges ([#28](https://github.com/climate-resource/input4mips_validation/pull/28))
- Updated conda install workflow README badge ([#29](https://github.com/climate-resource/input4mips_validation/pull/29))
- Updated licence badge and tweaked badge layout ([#30](https://github.com/climate-resource/input4mips_validation/pull/30))

### 🔧 Trivial/Internal Changes

- [#26](https://github.com/climate-resource/input4mips_validation/pull/26), [#32](https://github.com/climate-resource/input4mips_validation/pull/32), [#33](https://github.com/climate-resource/input4mips_validation/pull/33)


## Input4MIPs validation v0.7.0 (2024-07-19)


### Features

- Added configuration so that a locked version of the package will be built too.

  The instructions in the README for installation from PyPI should now be valid.
  The instructions for installation from conda are still waiting on
  https://github.com/conda-forge/staged-recipes/pull/26986. ([#25](https://github.com/climate-resource/input4mips_validation/pull/25))

### Bug Fixes

- Fixed up version number, putting it back in line with PyPI ([#27](https://github.com/climate-resource/input4mips_validation/pull/27))

### Trivial/Internal Changes

- [#24](https://github.com/climate-resource/input4mips_validation/pull/24)


## Input4MIPs validation v0.5.2 (2024-07-19)


### Trivial/Internal Changes

- [#23](https://github.com/climate-resource/input4mips_validation/pull/23)


## Input4MIPs validation v0.5.1 (2024-07-19)


### Trivial/Internal Changes

- [#20](https://github.com/climate-resource/input4mips_validation/pull/20), [#22](https://github.com/climate-resource/input4mips_validation/pull/22)


## Input4MIPs validation v0.6.0 (2024-07-18)


### Breaking Changes

- Re-named {py:attr}`input5mips_validation.cvs_handling.input4MIPs.activity_id.ActivityIDValues.url` to {py:attr}`input4mips_validation.cvs_handling.input4MIPs.activity_id.ActivityIDValues.URL`
  i.e. "url" --> "URL" ([#17](https://github.com/climate-resource/input4mips_validation/pull/17))
- Loosened dependency pins ([#21](https://github.com/climate-resource/input4mips_validation/pull/21))

### Features

- Added handling of the institution ID controlled vocabulary ([#16](https://github.com/climate-resource/input4mips_validation/pull/16))
- Added handling of the futher_info_url within the context of the controlled vocabulary ([#18](https://github.com/climate-resource/input4mips_validation/pull/18))


## Input4MIPs validation v0.5.0 (2024-06-25)


### Breaking Changes

- Completely re-wrote the package in an attempt to better handle the controlled vocabularies (CVs).

  The key module is still {py:mod}`input4mips_validation.dataset`.

  However, we now also have {py:mod}`input4mips_validation.cvs_handling`, which we use for sanely handling the CVs.
  This package may be split out into a separate package in future. ([#15](https://github.com/climate-resource/input4mips_validation/pull/15))


## Input4MIPs validation v0.4.0 (2024-06-20)


### Bug Fixes

- * Pinned input4MIPs CVs source files to avoid unexpected breaking changes
  * Pinned numpy < 2 to fix up install

  ([#13](https://github.com/climate-resource/input4mips_validation/pull/13))


## Input4MIPs validation v0.3.4 (2024-05-24)


### Trivial/Internal Changes

- [#12](https://github.com/climate-resource/input4mips_validation/pull/12)


## Input4MIPs validation v0.3.3 (2024-05-23)


### Trivial/Internal Changes

- [#11](https://github.com/climate-resource/input4mips_validation/pull/11)


## Input4MIPs validation v0.3.2 (2024-05-22)


### Trivial/Internal Changes

- [#10](https://github.com/climate-resource/input4mips_validation/pull/10)


## Input4MIPs validation v0.3.1 (2024-04-23)


### Improvements

- Disabled grid validation while we wait to work out what it means ([#9](https://github.com/climate-resource/input4mips_validation/pull/9))


## Input4MIPs validation v0.3.0 (2024-04-23)


### Breaking Changes

- Switched to using [typer](https://typer.tiangolo.com/) for our CLI.

  This did not change the CLI,
  but it did include re-arranging a number of internal modules,
  hence this is a breaking change. ([#7](https://github.com/climate-resource/input4mips_validation/pull/7))

### Features

- Add support for yearly time bounds to {py:func}`input4mips_validation.xarray_helpers.add_time_bounds` ([#6](https://github.com/climate-resource/input4mips_validation/pull/6))

### Bug Fixes

- Fixed {py:func}`input4mips_validation.controlled_vocabularies.inference.infer_frequency`
  so it can handle the switch from Julian to Gregorian calendars
  (which affects the number of days in October 1582). ([#6](https://github.com/climate-resource/input4mips_validation/pull/6))

### Trivial/Internal Changes

- [#6](https://github.com/climate-resource/input4mips_validation/pull/6), [#8](https://github.com/climate-resource/input4mips_validation/pull/8)


## Input4MIPs validation v0.2.1 (2024-02-15)


### Bug Fixes

- Loosened dependencies ([#5](https://github.com/climate-resource/input4mips_validation/pull/5))


## Input4MIPs validation v0.2.0 (2024-02-09)


### Features

- Add structure required to support basic command-line interface.

  The command-line interface provides the command `input4mips-validation validate-file`. ([#2](https://github.com/climate-resource/input4mips_validation/pull/2))

### Bug Fixes

- Added LICENCE to the project ([#3](https://github.com/climate-resource/input4mips_validation/pull/3))


## Input4MIPs validation v0.1.1 (2024-02-06)


No significant changes.
