"""Automatically updates pyproject astrolib.py version"""
import tempfile
import os
from pathlib import Path

import click
from tomlkit import parse, dumps

PYPROJECT_FILE = (Path(".").parent / "pyproject.toml").resolve()


class SafeOpen:
    """Open a file to be edited and replaced safely.
    Instead of change the file context, it will create a new on and rename it at the end of
    the modification process.
    """

    def __init__(self, path, mode="w+b"):  # noqa
        self._target = path
        self._mode = mode

    def __enter__(self):
        """Context manager entry point."""
        self._file = tempfile.NamedTemporaryFile(mode=self._mode, delete=False)
        return self._file

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point.

        Here we close the file and check if there is no exception. If no, we rename the
        original target file, otherwise we delete the recently created temp file.
        """
        self._file.close()
        if exc_type is None:
            os.rename(self._file.name, self._target)
        else:
            os.unlink(self._file.name)


def update_version():
    def get_new_version(current_version):
        """Extract version from branch name"""
        # version format > bump_version_0-0-2
        upgrade_version = current_version.split(".")
        upgrade_version[-1] = str(int(upgrade_version[-1]) + 1)
        return ".".join(upgrade_version)

    with open(PYPROJECT_FILE) as f:
        pyproject = parse(f.read())
        with SafeOpen(PYPROJECT_FILE, "w") as f:
            current_version = pyproject["tool"]["poetry"]["version"]
            new_version = get_new_version(current_version)
            pyproject["tool"]["poetry"]["version"] = new_version
            f.write(dumps(pyproject))
    return {"old_version": current_version, "new_version": new_version}


@click.command()
@click.option("--major")
def main(major=False):
    versions = update_version()
    print(f"Bumps astrolib.py to {versions['new_version']}")


if __name__ == "__main__":
    main()
