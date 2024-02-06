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

**Other info :**
[![License](https://img.shields.io/github/license/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/commits/main)
[![Contributors](https://img.shields.io/github/contributors/climate-resource/input4mips_validation.svg)](https://github.com/climate-resource/input4mips_validation/graphs/contributors)


<!--- sec-end-description -->

Full documentation can be found at:
[input4mips-validation.readthedocs.io](https://input4mips-validation.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

## Installation

<!--- sec-begin-installation -->

Input4MIPs-validation can be installed with conda or pip:

```bash
pip install input4mips-validation
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

For development, we rely on [poetry](https://python-poetry.org) for all our
dependency management. To get started, you will need to make sure that poetry
is installed
([instructions here](https://python-poetry.org/docs/#installing-with-the-official-installer),
we found that pipx and pip worked better to install on a Mac).

For all of work, we use our `Makefile`.
You can read the instructions out and run the commands by hand if you wish,
but we generally discourage this because it can be error prone.
In order to create your environment, run `make virtual-environment`.

If there are any issues, the messages from the `Makefile` should guide you
through. If not, please raise an issue in the [issue tracker][issue_tracker].

For the rest of our developer docs, please see [](development-reference).

[issue_tracker]: https://github.com/climate-resource/input4mips_validation/issues

<!--- sec-end-installation-dev -->
