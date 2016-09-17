# Core modules
import argparse
import sys
from os import getcwd
from glob import glob

# Local modules
from .parsers import parse_docs_repo


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
        '--media-destination',
        required=True,
        help=(
            "An alternate location to place media inside the "
            "destination folder."
        )
    )
    parser.add_argument(
        '--source-branch', help="The branch to clone."
    )
    parser.add_argument(
        '--build-path',
        default=".", help="A folder for the compiled HTML files"
    )
    parser.add_argument(
        '--template-path',
        help="Path to a local wrapper HTML template."
    )
    parser.add_argument(
        '--nav-path',
        help="Path to a local nav file."
    )
    parser.add_argument(
        '--files-folder',
        default="src", help="Where to look for files within the repository."
    )
    parser.add_argument(
        '--media-folder',
        default="media", help="Where to look for media."
    )
    parser.add_argument(
        '--relative-media-destination',
        help="Relative path to media for built documents."
    )

    return parser.parse_args()


def preprocess_files(dir_path, preprocessor_string):
    """
    Given a directory path and a string representing a python function,
    run each file in the directory through the function.
    """

    (package, function) = preprocessor_string.split(':')
    sys.path.append(getcwd())
    preprocessor = getattr(__import__(package), function)

    for filename in glob(dir_path + '/**/*.md', recursive=True):
        preprocessor(filename)


def main():
    """
    The starting point for the documentation-parser.
    Intended to be run through the command-line.
    """

    arguments = parse_arguments()
    parse_docs_repo(**vars(arguments))


if __name__ == "__main__":
    main()
