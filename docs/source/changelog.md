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
