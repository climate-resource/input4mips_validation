# Input4MIPs-validation

<!---
Can use start-after and end-before directives in docs, see
https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#inserting-other-documents-directly-into-the-current-document
-->

<!--- sec-begin-description -->

Validation of input4MIPs data (checking file formats, metadata etc.).



[![CI](https://github.com/climate-resource/input4mips_validation/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/climate-resource/input4mips_validation/actions/workflows/ci.yaml)
[![Coverage](https://codecov.io/gh/climate-resource/input4mips_validation/branch/main/graph/badge.svg)](https://codecov.io/gh/climate-resource/input4mips_validation)
[![Docs](https://readthedocs.org/projects/input4mips-validation/badge/?version=latest)](https://input4mips-validation.readthedocs.io)

**PyPI :**
[![PyPI](https://img.shields.io/pypi/v/input4mips-validation.svg)](https://pypi.org/project/input4mips-validation/)
[![PyPI: Supported Python versions](https://img.shields.io/pypi/pyversions/input4mips-validation.svg)](https://pypi.org/project/input4mips-validation/)
[![PyPI install](https://github.com/climate-resource/input4mips_validation/actions/workflows/install.yaml/badge.svg?branch=main)](https://github.com/climate-resource/input4mips_validation/actions/workflows/install.yaml)

**Conda :**
[![Conda](https://img.shields.io/conda/vn/conda-forge/input4mips-validation.svg)](https://anaconda.org/conda-forge/input4mips-validation)
[![Conda platforms](https://img.shields.io/conda/pn/conda-forge/input4mips-validation.svg)](https://anaconda.org/conda-forge/input4mips-validation)
[![Conda install](https://github.com/climate-resource/input4mips_validation/workflows/Test%20conda%20install/badge.svg)](https://github.com/climate-resource/input4mips_validation/actions?query=workflow%3A%22Test+conda+install%22)

**Other info :**
[![Licence](https://img.shields.io/badge/Licence-003366)](https://github.com/climate-resource/input4mips_validation/blob/main/LICENCE)
[![Last Commit](https://img.shields.io/github/last-commit/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/commits/main)
[![Contributors](https://img.shields.io/github/contributors/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/graphs/contributors)


<!--- sec-end-description -->

Full documentation can be found at:
[input4mips-validation.readthedocs.io](https://input4mips-validation.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

## Installation
<!--- sec-begin-installation -->

### As an application

If you want to use input4MIPs-validation as an application,
for example you just want to use its command-line interface,
then we recommend using the 'locked' version of the package.
This version pins the version of all dependencies too,
which reduces the chance of installation issues
because of breaking updates to dependencies.

The locked version of input4mips-validation can be installed with

```bash
# pip: https://pip.pypa.io/en/stable/
pip install input4mips-validation[locked]
# mamba: https://mamba.readthedocs.io/en/latest/
mamba install -c conda-forge input4mips-validation-locked
# conda: https://docs.conda.io/projects/conda/en/stable/
conda install -c conda-forge input4mips-validation-locked
```

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

```bash
# pip: https://pip.pypa.io/en/stable/
pip install input4mips-validation
# mamba: https://mamba.readthedocs.io/en/latest/
mamba install -c conda-forge input4mips-validation
# conda: https://docs.conda.io/projects/conda/en/stable/
conda install -c conda-forge input4mips-validation
```

Additional dependencies can be installed using

```bash
# To add plotting dependencies
pip install input4mips-validation[plots]
# To add notebook dependencies
pip install input4mips-validation[notebooks]

# If you are installing with conda, we recommend
# installing the extras by hand because there is no stable
# solution yet (issue here: https://github.com/conda/conda/issues/7502)
```

<!--- sec-end-installation -->

### For developers

<!--- sec-begin-installation-dev -->

For development, we rely on [pixi](https://pixi.sh/latest/)
for all our dependency management.
To get started, you will need to make sure that pixi is installed
([instructions here](https://pixi.sh/latest/#installation)).

We rely on [pdm](https://pdm-project.org/en/latest/) for managing our PyPI builds.
Hence, you will also need to make sure that pdm is installed on your system
([instructions here](https://pdm-project.org/en/latest/#installation),
although we found that installing with [pipx](https://pipx.pypa.io/stable/installation/)
worked perfectly for us).

For all of work, we use our `Makefile`.
You can read the instructions out and run the commands by hand if you wish,
but we generally discourage this because it can be error prone.
In order to create your environment, run `make virtual-environment`.

If there are any issues, the messages from the `Makefile` should guide you
through. If not, please raise an issue in the
[issue tracker](https://github.com/climate-resource/input4mips_validation/issues).

For the rest of our developer docs, please see [](development-reference).

<!--- sec-end-installation-dev -->
