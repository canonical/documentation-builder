# Core modules
import argparse
import tempfile
from os.path import join

# Third party modules
from git import Repo

# Local modules
from .mdbuild import build


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
        nargs=1, required=True,
        help="Git repository URL for retrieving markdown files."
    )
    parser.add_argument(
        '--files-path',
        default="src",
        nargs=1, help="Where to look for files within the repository."
    )
    parser.add_argument(
        '--destination-folder',
        nargs=1, default=".", help="A folder for the compiled HTML files"
    )

    return parser.parse_args()


def main():
    """
    The starting point for the documentation-parser.
    Intended to be run through the command-line.
    """

    arguments = parse_arguments()

    source_folder = tempfile.mkdtemp()
    Repo.clone_from(arguments.source_repository, source_folder)

    build(
        source=join(source_folder, arguments.files_path.strip('/')),
        outpath=arguments.destination_folder
    )


if __name__ == "__main__":
    main()
