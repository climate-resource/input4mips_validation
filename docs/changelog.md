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
