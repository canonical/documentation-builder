# Core modules
import argparse
import sys
from os import getcwd, path
from glob import glob
import pkg_resources

# Local modules
from .builder import build


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
        default='.',
        help="Path to the folder containing markdown files (default: .)"
    )
    parser.add_argument(
        '--source-media-dir',
        default="media",
        help="Path to the folder containing media files (default: ./media)"
    )
    parser.add_argument(
        '--output-path',
        default="build",
        help="Destination path for the built HTML files (default: .)"
    )
    parser.add_argument(
        '--output-media-path',
        help="Where to put media files (default: ./build/media)"
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
    parser.add_argument(
        '--ignore-file',
        action='append',
        default=['README.md'],
        dest='ignore_files',
        help=(
            "Filename of a markdown file to ignore and not parse into HTML. "
            "Can be declared multiple times."
        )
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help="Show the currently installed version"
    )

    arguments = vars(parser.parse_args())

    if arguments['version']:
        print(
            pkg_resources.get_distribution(
                "ubuntudesign.documentation_builder"
            ).version
        )
        sys.exit()
    else:
        del arguments['version']

    if not arguments['output_media_path']:
        arguments['output_media_path'] = path.join(
            arguments['output_path'], 'media'
        )

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
    build(**arguments)


if __name__ == "__main__":
    main()
