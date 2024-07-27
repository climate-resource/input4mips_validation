"""
Write a file we can use as our docs building environment on RtD
"""

from __future__ import annotations

import typer
import yaml


def main() -> None:
    """
    Write our docs environment file for Read the Docs
    """
    PIXI_LOCK_FILE = "pixi.lock"
    DOCS_ENVIRONMENT_FILE = "environment-docs.yml"

    with open(PIXI_LOCK_FILE) as fh:
        pixi_lock_info = yaml.safe_load(fh)

    docs_env_info = pixi_lock_info["environments"]["docs"]

    conda_dependencies = ["pip=24.0"]
    pypi_dependencies = []
    for dependency in docs_env_info["packages"]["linux-64"]:
        # for dependency in docs_env_info["packages"]["osx-arm64"]:
        if "conda" in dependency:
            if not dependency["conda"].endswith(".conda"):
                # files that are bundled (e.g. tar files),
                # not something conda supports I don't think
                continue

            base = dependency["conda"].split("/")[-1]
            toks = base.split(".conda")[0].split("-")
            id = f"{'-'.join(toks[:-2])}={toks[-2]}={toks[-1]}"
            conda_dependencies.append(id)

        if "pypi" in dependency:
            if dependency["pypi"] == ".":
                # Self, can move on
                continue

            # Exceptions :)
            if "loguru" in dependency["pypi"] and "config" in dependency["pypi"]:
                base = dependency["pypi"].split("/")[-1].split(".tar.gz")[0]
                toks = base.split("-")
                id = f"{'-'.join(toks[:-1])}=={toks[-1]}"

            elif dependency["pypi"].endswith(".tar.gz"):
                # some tar file, ignore
                continue

            else:
                base = dependency["pypi"].split("/")[-1]
                toks = base.split("-")
                id = f"{toks[0]}=={toks[1]}"

            pypi_dependencies.append(id)

    out = {}

    if docs_env_info["channels"] != [
        {"url": "https://conda.anaconda.org/conda-forge/"}
    ]:
        raise NotImplementedError()

    out["channels"] = ["conda-forge"]
    out["dependencies"] = [*conda_dependencies, {"pip": pypi_dependencies}]

    with open(DOCS_ENVIRONMENT_FILE, "w") as fh:
        yaml.dump(out, fh)


if __name__ == "__main__":
    typer.run(main)
