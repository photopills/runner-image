import json
import os
from types import new_class
import warnings
import asyncio
import time
from pathlib import Path

import tomlkit
from invoke import task
from git import Repo as _Repo
from .github import create_new_release as gh_create_new_release
from .github import create_pull_request, get_last_release_tag


def get_current_repo():
    "Generic resolver to select the appropriated file type"
    pyproject_file = Path(".").parent / "pyproject.toml"
    package_file = Path(".").parent / "package.json"
    version_file_path = ""
    if pyproject_file.exists():
        version_file_path = pyproject_file.resolve()
    elif package_file.exists():
        version_file_path = package_file.resolve()

    return Path(version_file_path).parent.name


def get_current_version():
    """Returns library version"""
    pyproject_file = Path(".").parent / "pyproject.toml"
    package_file = Path(".").parent / "package.json"
    if pyproject_file.exists():
        version_file = pyproject_file.resolve()
        with open(version_file) as f:
            pyproject = tomlkit.parse(f.read())
            return pyproject["tool"]["poetry"]["version"]
    elif package_file.exists():
        version_file = package_file.resolve()
        with open(version_file) as f:
            package = json.loads(f.read())
            return package["version"]


@task
def update_astrolib_wrapper(ctx, major=False):
    def get_new_version(current_version):
        """Create a new version number by adding on value to the current minor number"""
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

    versions = update_version()
    print(versions["new_version"])


@task
def create_new_release():
    """Create a new library release

    Currently can do the release for astrolib.py and astrolib3.js
    """
    repo = get_current_repo()
    version = get_current_version()
    asyncio.run(gh_create_new_release(version, repo))


@task
def update_astrolib(ctx, new_version):
    def update_astrolib_version(new_version):
        pyproject_file = (Path(".").parent / "pyproject.toml").resolve()
        with open(pyproject_file) as f:
            pyproject = tomlkit.parse(f.read())
        with open(pyproject_file, "w+") as f:
            old_version = pyproject["tool"]["poetry"]["dependencies"]["astrolib"]["rev"]
            pyproject["tool"]["poetry"]["dependencies"]["astrolib"]["rev"] = new_version
            f.write(tomlkit.dumps(pyproject))
        return {"old_version": old_version, "new_version": new_version}

    versions = update_astrolib_version(new_version)
    # create new release
    print(versions["new_version"])


@task
def update_dependency(ctx, library):
    def update_astrolib_version(new_version):
        "Update pyproject file version"
        pyproject_file = (Path(".").parent / "pyproject.toml").resolve()
        with open(pyproject_file) as f:
            pyproject = tomlkit.parse(f.read())
        with open(pyproject_file, "w+") as f:
            old_version = pyproject["tool"]["poetry"]["dependencies"]["astrolib"]["rev"]
            pyproject["tool"]["poetry"]["dependencies"]["astrolib"]["rev"] = new_version
            f.write(tomlkit.dumps(pyproject))
        return {"old_version": old_version, "new_version": new_version}

    class Repo:
        def __init__(self) -> None:
            self.local = _Repo(".")
            self.starting_branch = self.local.head.ref
            self.master = self.checkout_to_master()
            self.origin = self.authenticated_origin()

        @property
        def name(self):
            """Assumes that local repo name is the same that remote repo"""
            return self.local.working_dir.rsplit("/", 1)[-1]

        @property
        def local_branches(self):
            """Returns all repo branches"""
            return self.local.heads

        @property
        def remote_branches(self):
            """Returns all repo branches"""
            return self.origin.refs

        def checkout_to_master(self):
            # TODO: Check if repo is_dirty, but it should be cleaned
            # checkout to master if need
            active_branch = self.local.active_branch
            if active_branch.name != "master":
                print("Checkout to master")
                master = self.local_branches.master
                master.checkout()
            else:
                master = active_branch
            self.master = master
            print(f"Starting from branch: {self.local.active_branch}")
            return self.master

        def authenticated_origin(self):
            # ensures that we are authenticated
            origin = self.local.remotes[0]
            GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
            origin.set_url(f"https://{GITHUB_TOKEN}@github.com/photopills/{self.name}")
            self.origin = origin
            return self.origin

        def create_branch(self, new_version):
            branch_name = f"auto/bumps_to_version_{new_version}"
            return self.local.create_head(branch_name)

        def commit_all_changes(self, message):
            changed_files = self.local.index.diff(None)
            for file in changed_files:
                self.local.index.add(file.b_path)
            self.local.index.commit(message)

        def clean_local_repo(self, branch: str):
            """Clean update version branch

            Is automatically called if the push to remote succeeded
            """
            print("Starting cleaning repo after push")
            self.checkout_to_master()
            print(f"Current branch: {self.local.active_branch}")

            # delete version update branch
            self.local.delete_head(branch, force=True)

        def checkout_to_branch(self, branch_name, remote=True):
            if remote:
                branches = self.remote_branches
            for branch in branches:
                if branch_name in branch.name:
                    return branch.checkout("--track")
            raise AttributeError(f"There isn't any branch with name {branch_name}")

        def push(self, branch, force=True):
            """Push branch with updated version to remote repository"""
            info = self.origin.push(branch, force=force)
            summary = info[0].summary
            # TODO: Create regex to match summary SHA format: b18565a..34b8681
            if ".." in summary:
                ## everything went well, we can checkout to master and delete the
                # local branch
                self.clean_local_repo(branch)
            else:
                warnings.warn(
                    "There wasn't possible push the changes",
                    f"Push info: {summary}",
                )
            return self

    ## main
    repo = Repo()
    assert repo.name == library, "Local repository and library name should be the same"
    # get new release tag from github
    new_version = asyncio.run(get_last_release_tag(repo.name))
    # update repo
    repo.origin.fetch()
    # create new branch to apply the version update
    branch = repo.create_branch(new_version)

    versions = update_astrolib_version(new_version)
    commit_message = (
        f"Bumps {library} from {versions['old_version']} to {versions['new_version']}"
    )
    ## end code specific to this repo
    repo.commit_all_changes(message=commit_message)
    # update lock file
    # fmt: off
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    ctx.run(f"git config --global url.'https://{GITHUB_TOKEN}@github.com/'.insteadOf 'https://github.com/'")  # noqa
    ctx.run("poetry update astrolib")
    ctx.run(f"git config --global --unset url.'https://{GITHUB_TOKEN}@github.com/'.insteadOf") # noqa
    # fmt: on
    repo.clean_local_repo(branch)
    repo.push(branch, force=True)
    # create_pull request
    time.sleep(1)
    asyncio.run(
        create_pull_request(
            branch.name, repo.name, versions["old_version"], versions["new_version"]
        )
    )
