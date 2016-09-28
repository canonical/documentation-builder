# Core modules
import argparse
import sys
from os import getcwd
from glob import glob

# Local modules
from .build import build


def parse_arguments():
    """
    Parse command-line options for documentation-parser command-line script
    """

    parser = argparse.ArgumentParser(
        description=(
            "A tool to build documentation HTML files from markdown files, "
            "either from a local directory or a remote repository."
        )
    )

    parser.add_argument(
        '--repository',
        help=(
            "Build files from a remote repository instead of a local folder"
        )
    )
    parser.add_argument(
        '--branch',
        help=(
            "Pull from an alternative branch to the default"
            "Only valid with --repository."
        )
    )
    parser.add_argument(
        '--source-path',
        help="Path to the folder containing markdown files (default: .)"
    )
    parser.add_argument(
        '--source-media-dir',
        default="media",
        help="Path to the folder containing media files (default: ./media)"
    )
    parser.add_argument(
        '--source-context-file',
        default="context.yaml",
        help="A file containing the context object for building the templates"
    )
    parser.add_argument(
        '--output-path',
        default=".",
        help="Destination path for the built HTML files (default: .)"
    )
    parser.add_argument(
        '--output-media-dir',
        default="media",
        help="Where to put media files (default: ./media)"
    )
    parser.add_argument(
        '--template-path',
        help="Path to an alternate wrapping template for the built HTML files"
    )
    parser.add_argument(
        '--media-url',
        help=(
            "Prefix for linking to media inside the built HTML files "
            "(default: Relative path to built media location, e.g.: ../media)"
        )
    )
    parser.add_argument(
        '--no-link-extensions',
        action='store_true',
        help="Don't include '.html' extension in internal links"
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help="Don't clean up temporary directory after cloning repository"
    )

    arguments = parser.parse_args()

    if not arguments.source_path:
        if not arguments.repository:
            parser.error(
                "At least one of --repository or --source-path is required."
            )
        else:
            arguments.source_path = '.'

    return arguments


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
    build(**vars(arguments))


if __name__ == "__main__":
    main()
