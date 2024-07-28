"""
Write out the pins for our conda recipe

These can be copy-pasted into the locked info at
https://github.com/conda-forge/input4mips-validation-feedstock/blob/main/recipe/meta.yaml
"""

from __future__ import annotations

import tomli
import typer
import yaml
from packaging.version import Version


def main() -> None:
    """
    Write our docs environment file for Read the Docs
    """
    PYPROJECT_TOML_FILE = "pyproject.toml"
    PIXI_LOCK_FILE = "pixi.lock"

    with open(PYPROJECT_TOML_FILE, "rb") as fh:
        pyproject_toml = tomli.load(fh)

    with open(PIXI_LOCK_FILE) as fh:
        pixi_lock_info = yaml.safe_load(fh)

    name_map = {
        "scitools-iris": "iris",
        "cf-xarray": "cf_xarray",
        "pint-xarray": "pint_xarray",
    }
    for dependency in pyproject_toml["project"]["dependencies"]:
        package_name = (
            dependency.split(">")[0].split("<")[0].split(">=")[0].split("<=")[0]
        )
        if package_name in name_map:
            package_name = name_map[package_name]

        packages = [
            v
            for v in pixi_lock_info["environments"]["default"]["packages"]["linux-64"]
            if ("conda" in v and package_name in v["conda"])
            or ("pypi" in v and f"/{package_name}" in v["pypi"])
        ]
        if package_name == "loguru":
            packages = [v for v in packages if "loguru-config" not in v["pypi"]]

        if len(packages) != 1:
            print(f"Something wrong for {package_name}")
            # tmp = [
            #     v
            #     for v in pixi_lock_info["environments"]["default"]["packages"][
            #         "linux-64"
            #     ]
            #     if ("conda" in v and package_name in v["conda"])
            #     or ("pypi" in v and package_name in v["pypi"])
            # ]
            # breakpoint()
            continue

        dependency_desc = packages[0]
        if "conda" in dependency_desc:
            base = dependency_desc["conda"].split("/")[-1]
            toks = base.split(".tar.bz2")[0].split("-")
            version = toks[1]
            name = toks[0]

        elif "loguru-config" in dependency_desc["pypi"]:
            base = dependency_desc["pypi"].split("/")[-1]
            toks = base.split(".tar.gz")[0].split("-")
            version = toks[-1]
            name = "-".join(toks[:-1])

        else:
            base = dependency_desc["pypi"].split("/")[-1]
            toks = base.split("-py")[0].split("-")

            version = toks[1]
            name = toks[0]

        vv = Version(version)
        max_pin = f"{vv.major}.{vv.minor}.{vv.micro + 1}"
        print(
            f"- {{ pin_compatible('{name}', min_pin='{version}', max_pin='{max_pin}') }}"  # noqa: E501
        )


if __name__ == "__main__":
    typer.run(main)
