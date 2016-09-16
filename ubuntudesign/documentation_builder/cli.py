# Core modules
import argparse
import tempfile
from contextlib import contextmanager
from os.path import join
from shutil import rmtree

# Third party modules
from git import Repo

# Local modules
from .mdbuild import build


@contextmanager
def ephemeral_directory():
    temp_dir = tempfile.mkdtemp(prefix='/dev/shm/')
    try:
        yield temp_dir
    finally:
        rmtree(temp_dir)


def parse_arguments():
    """
    Parse command-line options for documentation-parser command-line script
    """

    parser = argparse.ArgumentParser(
        description=(
            "A tool to build documentation HTML files from markdown files "
            "stored in a repository somewhere"
        )
    )

    parser.add_argument(
        '--source-repository',
        required=True, help="Git repository URL for retrieving markdown files."
    )
    parser.add_argument(
        '--files-path',
        default="src", help="Where to look for files within the repository."
    )
    parser.add_argument(
        '--destination-folder',
        default=".", help="A folder for the compiled HTML files"
    )

    return parser.parse_args()


def main():
    """
    The starting point for the documentation-parser.
    Intended to be run through the command-line.
    """

    arguments = parse_arguments()

    with ephemeral_directory() as temp_source_folder:
        Repo.clone_from(arguments.source_repository, temp_source_folder)

        build(
            source=join(temp_source_folder, arguments.files_path.strip('/')),
            outpath=arguments.destination_folder
        )


if __name__ == "__main__":
    main()
