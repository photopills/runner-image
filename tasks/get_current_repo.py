from pathlib import Path


def main():
    """Returns library version"""
    repo_main_folder = Path(".").parent.resolve()
    return repo_main_folder.rsplit("/", 1)[-1]


if __name__ == "__main__":
    main()
