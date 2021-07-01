from pathlib import Path

import click
import tomlkit


def update_astrolib_version(new_version):
    pyproject_file = (Path(".").parent / "pyproject.toml").resolve()
    with open(pyproject_file) as f:
        pyproject = tomlkit.parse(f.read())
    with open(pyproject_file, "w+") as f:
        old_version = pyproject["tool"]["poetry"]["dependencies"]["astrolib"]["rev"]
        pyproject["tool"]["poetry"]["dependencies"]["astrolib"]["rev"] = new_version
        f.write(tomlkit.dumps(pyproject))
    return {"old_version": old_version, "new_version": new_version}


@click.command()
@click.argument("new_version")
def main(new_version):
    ## start code specific to this repo
    versions = update_astrolib_version(new_version)
    print(versions["new_version"])


if __name__ == "__main__":
    main()
