<!--- --8<-- [start:description] -->
# Input4MIPs-validation

Validation of input4MIPs data (checking file formats, metadata etc.).

**Key info :**
[![Docs](https://readthedocs.org/projects/input4mips-validation/badge/?version=latest)](https://input4mips-validation.readthedocs.io)
[![Main branch: supported Python versions](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fclimate-resource%2Finput4mips_validation%2Fmain%2Fpyproject.toml)](https://github.com/climate-resource/input4mips_validation/blob/main/pyproject.toml)
[![Licence](https://img.shields.io/pypi/l/input4mips-validation?label=licence)](https://github.com/climate-resource/input4mips_validation/blob/main/LICENCE)

**PyPI :**
[![PyPI](https://img.shields.io/pypi/v/input4mips-validation.svg)](https://pypi.org/project/input4mips-validation/)
[![PyPI install](https://github.com/climate-resource/input4mips_validation/actions/workflows/install-pypi.yaml/badge.svg?branch=main)](https://github.com/climate-resource/input4mips_validation/actions/workflows/install-pypi.yaml)

**Conda :**
[![Conda](https://img.shields.io/conda/vn/conda-forge/input4mips-validation.svg)](https://anaconda.org/conda-forge/input4mips-validation)
[![Conda platforms](https://img.shields.io/conda/pn/conda-forge/input4mips-validation.svg)](https://anaconda.org/conda-forge/input4mips-validation)
[![Conda install](https://github.com/climate-resource/input4mips_validation/actions/workflows/install-conda.yaml/badge.svg?branch=main)](https://github.com/climate-resource/input4mips_validation/actions/workflows/install-conda.yaml)

**Tests :**
[![CI](https://github.com/climate-resource/input4mips_validation/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/climate-resource/input4mips_validation/actions/workflows/ci.yaml)
[![Coverage](https://codecov.io/gh/climate-resource/input4mips_validation/branch/main/graph/badge.svg)](https://codecov.io/gh/climate-resource/input4mips_validation)

**Other info :**
[![Last Commit](https://img.shields.io/github/last-commit/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/commits/main)
[![Contributors](https://img.shields.io/github/contributors/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/graphs/contributors)

## Status

- development: the project is actively being worked on

As a user, please note that input4MIPs validation is undergoing heavy development.
This means that files which pass validation today may not pass in future.
While this will initially be frustrating, it will pay off in the long run
by helping us to create the cleanest, clearest set of data possible.
We hope that you can appreciate the importance of this too
(and we hope to get the effort it takes to do this
recognised at some point in the future too,
watch this space).
So, please enjoy the tool, please make use of it,
please [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new/choose)
whenever there is a problem,
but please also be ready to update your file writing scripts
when submitting the next round of files in three to six months' time.

<!--- --8<-- [end:description] -->

If you want to prepare your input4MIPs files for publication on ESGF,
please see
["How can I prepare my input4MIPs files for publication on ESGF?"](https://input4mips-validation.readthedocs.io/en/latest/how-to-guides/#how-can-i-prepare-my-input4mips-files-for-publication-on-esgf).

Full documentation can be found at:
[input4mips-validation.readthedocs.io](https://input4mips-validation.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

<!--- TODO: add link to preparing data for input4MIPs here -->

## Installation

<!--- --8<-- [start:installation] -->
### As an application

If you want to use input4MIPs-validation as an application,
for example you just want to use its command-line interface,
then we recommend using the 'locked' version of the package.
This version pins the version of all dependencies too,
which reduces the chance of installation issues
because of breaking updates to dependencies.

The locked version of input4mips-validation can be installed with

=== "mamba"
    ```sh
    mamba install -c conda-forge input4mips-validation-locked
    ```

    [mamba](https://mamba.readthedocs.io/en/latest/)
    is our recommend way to install the package
    because it has better handling of the compiled dependencies
    (like cfunits).

=== "conda"
    ```sh
    conda install -c conda-forge input4mips-validation-locked
    ```

    [conda](https://docs.conda.io/projects/conda/en/stable/)
    is a good way to install the package
    because it has better handling of the compiled dependencies
    (like cfunits).

=== "pip"
    ```sh
    pip install input4mips-validation[locked]
    ```

    [pip](https://pip.pypa.io/en/stable/)
    is a standard way to install Python packages.
    We make no guarantees that this will actually work
    because pip's handling of the compiled dependencies
    is not guaranteed.

### As a library

If you want to use input4MIPs-validation as a library,
for example you want to use it
as a dependency in another package/application that you're building,
then we recommend installing the package with the commands below.
This method provides the loosest pins possible of all dependencies.
This gives you, the package/application developer,
as much freedom as possible to set the versions of different packages.
However, the tradeoff with this freedom is that you may install
incompatible versions of input4mips-validation's dependencies
(we cannot test all combinations of dependencies,
particularly ones which haven't been released yet!).
Hence, you may run into installation issues.
If you believe these are because of a problem in input4mips-validation,
please [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new/choose).

The (non-locked) version of input4mips-validation can be installed with

=== "mamba"
    ```sh
    mamba install -c conda-forge input4mips-validation
    ```

    [mamba](https://mamba.readthedocs.io/en/latest/)
    is our recommend way to install the package
    because it has better handling of the compiled dependencies
    (like cfunits).

=== "conda"
    ```sh
    conda install -c conda-forge input4mips-validation
    ```

    [conda](https://docs.conda.io/projects/conda/en/stable/)
    is a good way to install the package
    because it has better handling of the compiled dependencies
    (like cfunits).

=== "pip"
    ```sh
    pip install input4mips-validation
    ```

    [pip](https://pip.pypa.io/en/stable/)
    is a standard way to install Python packages.
    We make no guarantees that this will actually work
    because pip's handling of the compiled dependencies
    is not guaranteed.

Additional dependencies can be installed using

=== "mamba"
    If you are installing with mamba, we recommend
    installing the extras by hand because there is no stable
    solution yet (see [conda issue #7502](https://github.com/conda/conda/issues/7502))

=== "conda"
    If you are installing with conda, we recommend
    installing the extras by hand because there is no stable
    solution yet (see [conda issue #7502](https://github.com/conda/conda/issues/7502))

=== "pip"
    ```sh
    # To add plotting dependencies
    pip install input4mips-validation[plots]
    # To add notebook dependencies
    pip install input4mips-validation[notebooks]
    ```

### For developers

For development, we rely on [pixi](https://pixi.sh/latest/)
for all our dependency management.
To get started, you will need to make sure that pixi is installed
([instructions here](https://pixi.sh/latest/#installation)).

We rely on [pdm](https://pdm-project.org/en/latest/) for managing our PyPI builds.
Hence, you will also need to make sure that pdm is installed on your system
([instructions here](https://pdm-project.org/en/latest/#installation),
although we found that installing with [pipx](https://pipx.pypa.io/stable/installation/)
worked perfectly for us).

For all of our work, we use our `Makefile`.
You can read the instructions out and run the commands by hand if you wish,
but we generally discourage this because it can be error prone.
In order to create your environment, run `make virtual-environment`.

If there are any issues, the messages from the `Makefile` should guide you
through. If not, please raise an issue in the
[issue tracker](https://github.com/climate-resource/input4mips_validation/issues).

For the rest of our developer docs, please see [development][development-reference].

<!--- --8<-- [end:installation] -->
