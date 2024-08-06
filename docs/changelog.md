# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.


<!--
You should *NOT* be adding new changelog entries to this file, this
file is managed by towncrier. See changelog/README.md.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news, md instead
of rst and use slightly different categories.
-->

<!-- towncrier release notes start -->

## input4mips-validation v0.11.3 (2024-08-06)


### 🎉 Improvements

- Made it explicit that [cftime](https://unidata.github.io/cftime/) and [typing-extensions](https://typing-extensions.readthedocs.io/en/latest/#) are required ([#59](https://github.com/climate-resource/input4mips_validation/pulls/59))

### 🐛 Bug Fixes

- Fixed up the writing of the `creation_time` attribute and datetime metadata inference to use the expected time format ([#60](https://github.com/climate-resource/input4mips_validation/pulls/60))

### 🔧 Trivial/Internal Changes

- [#60](https://github.com/climate-resource/input4mips_validation/pulls/60)


## input4mips-validation v0.11.2 (2024-08-05)


### 🔧 Trivial/Internal Changes

- [#57](https://github.com/climate-resource/input4mips_validation/pulls/57)


## input4mips-validation v0.11.1 (2024-08-03)

### 🎉 Improvements

- Added support for data without a time axis to
  [`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information]
  and [`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable]. ([#56](https://github.com/climate-resource/input4mips_validation/pulls/56))

### 🐛 Bug Fixes

- Fixed the type hint for `datetime_end`, `datetime_start` and `time_range`.
  These fields will now serialise and de-serialise correctly.
  Previously, if these fields were `None`, they were serialised and de-serialised as strings. ([#56](https://github.com/climate-resource/input4mips_validation/pulls/56))

### 🔧 Trivial/Internal Changes

- [#56](https://github.com/climate-resource/input4mips_validation/pulls/56)


## input4mips-validation v0.11.0 (2024-08-02)


### ⚠️ Breaking Changes

- - Removed the `--create-db-entry` flag from the `validate-file` command.
    Use the newly added `input4mips-validation db` commands to control the database instead.
  - Our databases our now multi-file, one file per file entry. This makes it much easier to track changes to the database.
    To load a database from a directory of files, use [`load_database_file_entries`][input4mips_validation.database.database.load_database_file_entries]
  - Changed the function signature of [`input4mips_validation.cvs.loading.load_cvs`][input4mips_validation.cvs.loading.load_cvs].
    Now it simply expects the `cv_source` rather than requiring a [`RawCVLoader`][input4mips_validation.cvs.loading_raw.RawCVLoader] as input.

  ([#55](https://github.com/climate-resource/input4mips_validation/pulls/55))

### 🆕 Features

- Added the ` --allow-cf-checker-warnings` flag to the `validate-file` and `validate-tree` commands.
  This allows the validation to pass, even if the CF-checker raises a warning.
  This was added because the CF-checker's warnings are sometimes overly strict. ([#52](https://github.com/climate-resource/input4mips_validation/pulls/52))
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

  ([#55](https://github.com/climate-resource/input4mips_validation/pulls/55))

### 🎉 Improvements

- - Updated the type and default value of
    [`Input4MIPsDatabaseEntryFile.validated_input4mips`][input4mips_validation.database.Input4MIPsDatabaseEntryFile.validated_input4mips]
    to clarify the different states of validation.
  - Parallelised [`create_db_file_entries`][input4mips_validation.database.creation.create_db_file_entries]

  ([#55](https://github.com/climate-resource/input4mips_validation/pulls/55))

### 🐛 Bug Fixes

- Fixed a missing f-string marker in `validate-tree`'s logging. ([#52](https://github.com/climate-resource/input4mips_validation/pulls/52))
- - Set `use_cftime=True` whenever we call `xr.open_dataset` to avoid spurious warnings
  - Only pass the directory to `extract_metadata_from_path` in [`DRS.validate_file_written_according_to_drs`][input4mips_validation.cvs.drs.DataReferenceSyntax.validate_file_written_according_to_drs].
    This helps reduce the chance of incorrecetly parsing the metadata.

  ([#55](https://github.com/climate-resource/input4mips_validation/pulls/55))

### 📚 Improved Documentation

- Clarified the meaning of the `timestamp` and `version` fields in our database entries ([#54](https://github.com/climate-resource/input4mips_validation/pulls/54))
- Added documentation for how to manage a database ([#55](https://github.com/climate-resource/input4mips_validation/pulls/55))

### 🔧 Trivial/Internal Changes

- [#55](https://github.com/climate-resource/input4mips_validation/pulls/55)


## input4mips-validation v0.10.2 (2024-07-28)


### 🐛 Bug Fixes

- Make [loguru-config](https://github.com/erezinman/loguru-config) an optional dependency in `pyproject.toml` too ([#50](https://github.com/climate-resource/input4mips_validation/pulls/50))

### 🔧 Trivial/Internal Changes

- [#50](https://github.com/climate-resource/input4mips_validation/pulls/50)


## input4mips-validation v0.10.1 (2024-07-28)


### 🎉 Improvements

- Clarify handling of dry run in [`upload_ftp`][input4mips_validation.upload_ftp] ([#45](https://github.com/climate-resource/input4mips_validation/pulls/45))
- [loguru-config](https://github.com/erezinman/loguru-config)
  is now an optional dependency.
  This makes it possible to install the package from conda
  without things exploding, as loguru-config is not available on conda.
  This may be changed in future, if loguru-config is released on conda
  (relevant MR here: https://github.com/conda-forge/staged-recipes/pull/27110) ([#48](https://github.com/climate-resource/input4mips_validation/pulls/48))

### 🔧 Trivial/Internal Changes

- [#44](https://github.com/climate-resource/input4mips_validation/pulls/44), [#46](https://github.com/climate-resource/input4mips_validation/pulls/46), [#47](https://github.com/climate-resource/input4mips_validation/pulls/47), [#49](https://github.com/climate-resource/input4mips_validation/pulls/49)


## input4mips-validation v0.10.0 (2024-07-27)


### ⚠️ Breaking Changes

- - Removed `--verbose` option from the `input4mips-validation` command
  - Moved logging to `input4mips_validation.logging`

  ([#40](https://github.com/climate-resource/input4mips_validation/pulls/40))

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

  ([#40](https://github.com/climate-resource/input4mips_validation/pulls/40))
- - Added the `input4mips-validation upload-ftp` command
  - Added [`input4mips_validation.upload_ftp`][input4mips_validation.upload_ftp]

  ([#43](https://github.com/climate-resource/input4mips_validation/pulls/43))

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

  ([#40](https://github.com/climate-resource/input4mips_validation/pulls/40))

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

  ([#40](https://github.com/climate-resource/input4mips_validation/pulls/40))

### 📚 Improved Documentation

- Updated README so that the snippet comments don't show up ([#37](https://github.com/climate-resource/input4mips_validation/pulls/37))
- - Added docs about project status to the README
  - Added docs about preparing a file in the how-to guides. How to upload will come in the next MR.
      - See ["How can I prepare my input4MIPs files for publication on ESGF?"](https://input4mips-validation.readthedocs.io/en/latest/how-to-guides/#how-can-i-prepare-my-input4mips-files-for-publication-on-esgf)

  ([#40](https://github.com/climate-resource/input4mips_validation/pulls/40))
- Added documentation about how to upload to an FTP server, and cross-linked these with the rest of the docs ([#43](https://github.com/climate-resource/input4mips_validation/pulls/43))

### 🔧 Trivial/Internal Changes

- [#40](https://github.com/climate-resource/input4mips_validation/pulls/40)


## input4mips-validation v0.9.0 (2024-07-24)


### 🆕 Features

- Added the `validate-tree` and `create-db` commands.

  These allow you to validate a tree of files
  and create a database of the files in the tree.

  Use the following commands to get help:

  - `input4mips-validation validate-tree --help`
  - `input4mips-validation create-db --help`

  ([#36](https://github.com/climate-resource/input4mips_validation/pulls/36))

### 📚 Improved Documentation

- - Updated the installation instructions now that we have a
    [conda package](https://anaconda.org/conda-forge/input4mips-validation).
  - Generally cleaned up the docs

  ([#36](https://github.com/climate-resource/input4mips_validation/pulls/36))

### 🔧 Trivial/Internal Changes

- [#36](https://github.com/climate-resource/input4mips_validation/pulls/36)


## input4mips-validation v0.8.1 (2024-07-22)


### 🔧 Trivial/Internal Changes

- [#34](https://github.com/climate-resource/input4mips_validation/pulls/34)


## input4mips-validation v0.8.0 (2024-07-22)


### ⚠️ Breaking Changes

- Completely re-wrote the package.

  The APIs are similar, but not identical.
  Given there are no users, we don't provide a migration guide.

  Key changes:

  - cleaned up the API to make clearer the different elements
  - changed dev tooling to supporting conda packages, because we needed iris

  ([#31](https://github.com/climate-resource/input4mips_validation/pulls/31))

### 📚 Improved Documentation

- Updated README badges ([#28](https://github.com/climate-resource/input4mips_validation/pulls/28))
- Updated conda install workflow README badge ([#29](https://github.com/climate-resource/input4mips_validation/pulls/29))
- Updated licence badge and tweaked badge layout ([#30](https://github.com/climate-resource/input4mips_validation/pulls/30))

### 🔧 Trivial/Internal Changes

- [#26](https://github.com/climate-resource/input4mips_validation/pulls/26), [#32](https://github.com/climate-resource/input4mips_validation/pulls/32), [#33](https://github.com/climate-resource/input4mips_validation/pulls/33)


## input4mips-validation v0.7.0 (2024-07-19)


### Features

- Added configuration so that a locked version of the package will be built too.

  The instructions in the README for installation from PyPI should now be valid.
  The instructions for installation from conda are still waiting on
  https://github.com/conda-forge/staged-recipes/pull/26986. ([#25](https://github.com/climate-resource/input4mips_validation/pulls/25))

### Bug Fixes

- Fixed up version number, putting it back in line with PyPI ([#27](https://github.com/climate-resource/input4mips_validation/pulls/27))

### Trivial/Internal Changes

- [#24](https://github.com/climate-resource/input4mips_validation/pulls/24)


## input4mips-validation v0.5.2 (2024-07-19)


### Trivial/Internal Changes

- [#23](https://github.com/climate-resource/input4mips_validation/pulls/23)


## input4mips-validation v0.5.1 (2024-07-19)


### Trivial/Internal Changes

- [#20](https://github.com/climate-resource/input4mips_validation/pulls/20), [#22](https://github.com/climate-resource/input4mips_validation/pulls/22)


## input4mips-validation v0.6.0 (2024-07-18)


### Breaking Changes

- Re-named {py:attr}`input5mips_validation.cvs_handling.input4MIPs.activity_id.ActivityIDValues.url` to {py:attr}`input4mips_validation.cvs_handling.input4MIPs.activity_id.ActivityIDValues.URL`
  i.e. "url" --> "URL" ([#17](https://github.com/climate-resource/input4mips_validation/pulls/17))
- Loosened dependency pins ([#21](https://github.com/climate-resource/input4mips_validation/pulls/21))

### Features

- Added handling of the institution ID controlled vocabulary ([#16](https://github.com/climate-resource/input4mips_validation/pulls/16))
- Added handling of the futher_info_url within the context of the controlled vocabulary ([#18](https://github.com/climate-resource/input4mips_validation/pulls/18))


## input4mips-validation v0.5.0 (2024-06-25)


### Breaking Changes

- Completely re-wrote the package in an attempt to better handle the controlled vocabularies (CVs).

  The key module is still {py:mod}`input4mips_validation.dataset`.

  However, we now also have {py:mod}`input4mips_validation.cvs_handling`, which we use for sanely handling the CVs.
  This package may be split out into a separate package in future. ([#15](https://github.com/climate-resource/input4mips_validation/pulls/15))


## input4mips-validation v0.4.0 (2024-06-20)


### Bug Fixes

- * Pinned input4MIPs CVs source files to avoid unexpected breaking changes
  * Pinned numpy < 2 to fix up install

  ([#13](https://github.com/climate-resource/input4mips_validation/pulls/13))


## input4mips-validation v0.3.4 (2024-05-24)


### Trivial/Internal Changes

- [#12](https://github.com/climate-resource/input4mips_validation/pulls/12)


## input4mips-validation v0.3.3 (2024-05-23)


### Trivial/Internal Changes

- [#11](https://github.com/climate-resource/input4mips_validation/pulls/11)


## input4mips-validation v0.3.2 (2024-05-22)


### Trivial/Internal Changes

- [#10](https://github.com/climate-resource/input4mips_validation/pulls/10)


## input4mips-validation v0.3.1 (2024-04-23)


### Improvements

- Disabled grid validation while we wait to work out what it means ([#9](https://github.com/climate-resource/input4mips_validation/pulls/9))


## input4mips-validation v0.3.0 (2024-04-23)


### Breaking Changes

- Switched to using [typer](https://typer.tiangolo.com/) for our CLI.

  This did not change the CLI,
  but it did include re-arranging a number of internal modules,
  hence this is a breaking change. ([#7](https://github.com/climate-resource/input4mips_validation/pulls/7))

### Features

- Add support for yearly time bounds to {py:func}`input4mips_validation.xarray_helpers.add_time_bounds` ([#6](https://github.com/climate-resource/input4mips_validation/pulls/6))

### Bug Fixes

- Fixed {py:func}`input4mips_validation.controlled_vocabularies.inference.infer_frequency`
  so it can handle the switch from Julian to Gregorian calendars
  (which affects the number of days in October 1582). ([#6](https://github.com/climate-resource/input4mips_validation/pulls/6))

### Trivial/Internal Changes

- [#6](https://github.com/climate-resource/input4mips_validation/pulls/6), [#8](https://github.com/climate-resource/input4mips_validation/pulls/8)


## input4mips-validation v0.2.1 (2024-02-15)


### Bug Fixes

- Loosened dependencies ([#5](https://github.com/climate-resource/input4mips_validation/pulls/5))


## input4mips-validation v0.2.0 (2024-02-09)


### Features

- Add structure required to support basic command-line interface.

  The command-line interface provides the command `input4mips-validation validate-file`. ([#2](https://github.com/climate-resource/input4mips_validation/pulls/2))

### Bug Fixes

- Added LICENCE to the project ([#3](https://github.com/climate-resource/input4mips_validation/pulls/3))


## input4mips-validation v0.1.1 (2024-02-06)


No significant changes.
