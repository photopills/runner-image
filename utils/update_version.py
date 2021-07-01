"""Automatically updates pyproject astrolib.py version"""
from pathlib import Path
import json
import click
import tomlkit


def get_new_version(current_version):
    """Extract version from branch name"""
    # version format > bump_version_0-0-2
    upgrade_version = current_version.split(".")
    upgrade_version[-1] = str(int(upgrade_version[-1]) + 1)
    return ".".join(upgrade_version)


def update_pyproject(version_file):
    """Updates Astrolib.py version"""
    with open(version_file) as f:
        pyproject = tomlkit.parse(f.read())
        with open(version_file, "w+") as f:
            current_version = pyproject["tool"]["poetry"]["version"]
            new_version = get_new_version(current_version)
            pyproject["tool"]["poetry"]["version"] = new_version
            f.write(tomlkit.dumps(pyproject))
    return {"old_version": current_version, "new_version": new_version}


def update_package(version_file):
    """Updates Astrolib3.js version"""
    with open(version_file) as f:
        package = json.loads(f.read())
        with open(version_file, "w+") as f:
            current_version = package["version"]
            new_version = get_new_version(current_version)
            package["version"] = new_version
            json.dump(package, f, indent=2)
    return {"old_version": current_version, "new_version": new_version}


def update_version():
    pyproject_file = Path(".").parent / "pyproject.toml"
    package_file = Path(".").parent / "package.json"
    if pyproject_file.exists():
        return update_pyproject(pyproject_file.resolve())
    elif package_file.exists():
        return update_package(package_file.resolve())


@click.command()
@click.option("--major")
def main(major=False):
    versions = update_version()
    print(versions["new_version"])


if __name__ == "__main__":
    main()
