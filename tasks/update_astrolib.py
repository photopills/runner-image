from pathlib import Path

import click
import tomlkit

"""Automatically updates pyproject astrolib.py version

This script should be called from terminal or from bash script with:
>> python update_version.py remote_branch_name --major=True/False

Or from python code:
from update_version import main
main(branch_name, major)

NOTE: This script should be called only when there is a new version release.

What does this script:
1. Loads the local git repo
2. Checkout to master (if needded)
3. Fetch origin/master to update local master
4. Create a new branch to performe the version update
5. Update pyproject.toml project version
6. Commit the new change
7. Push the new branch to remote repository

Once the new branch is pushed, the PR should be created by our bot or by a Tekton Task
"""
import warnings
import tempfile
import os
import click

from pathlib import Path

from tomlkit import parse, dumps
from git import RemoteProgress, Repo as _Repo


class MyProgressPrinter(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=""):
        print(
            op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE"
        )


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


def get_current_version() -> str:
    with open(PYPROJECT_FILE) as f:
        pyproject = parse(f.read())
    return pyproject["tool"]["poetry"]["version"]


def update_version(update_version_branch):
    new_version = update_version_branch.rsplit("-")[-1]
    with open(PYPROJECT_FILE) as f:
        pyproject = parse(f.read())
        with SafeOpen("./pyproject.toml", "w") as f:
            current_version = get_current_version()
            pyproject["tool"]["poetry"]["version"] = new_version
            f.write(dumps(pyproject))
    return {"old_version": current_version, "new_version": new_version}


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
        branch_name = f"bumps_to_version_{new_version}"
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
        # TODO: Add log

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


@click.command()
@click.option("--major")
@click.argument("branch_name")
def main(branch_name, major=False):
    ## main
    repo = Repo()
    # update repo
    repo.origin.fetch()
    branch = repo.checkout_to_branch(branch_name)
    ## start code specific to this repo
    versions = update_version(branch_name)
    commit_message = (
        f"Bumps astrolib.py from {versions['old_version']} to {versions['new_version']}"
    )
    ## end code specific to this repo

    repo.commit_all_changes(message=commit_message)
    repo.push(branch, force=True)

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
@click.argument("repo")
@click.argument("new_version")
def main(repo, new_version):
    ## start code specific to this repo
    versions = update_astrolib_version(new_version)
    print(f"Repo {repo}")
    print(versions["new_version"])


if __name__ == "__main__":
    main()
