"""Automatically updates pyproject astrolib.py version"""
from pathlib import Path

import click
from tomlkit import parse, dumps

PYPROJECT_FILE = (Path(".").parent / "pyproject.toml").resolve()


def update_version():
    def get_new_version(current_version):
        """Extract version from branch name"""
        # version format > bump_version_0-0-2
        upgrade_version = current_version.split(".")
        upgrade_version[-1] = str(int(upgrade_version[-1]) + 1)
        return ".".join(upgrade_version)

    with open(PYPROJECT_FILE, "r+") as f:
        pyproject = parse(f.read())
        current_version = pyproject["tool"]["poetry"]["version"]
        new_version = get_new_version(current_version)
        pyproject["tool"]["poetry"]["version"] = new_version
        f.write(dumps(pyproject))
    return {"old_version": current_version, "new_version": new_version}


@click.command()
@click.option("--major")
def main(major=False):
    versions = update_version()
    print(versions["new_version"])


if __name__ == "__main__":
    main()
