# Core modules
import argparse
import sys
import pkg_resources

# Local modules
from .builder import Builder


def parse_arguments(arguments):
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
        '--base-directory',
        help=(
            "The base path for the documentation repository "
            "(defaults to current directory)"
        )
    )
    parser.add_argument(
        '--source-folder',
        help=(
            "Path inside the base directory to the folder containing "
            "the markdown source files (default: .)"
        )
    )
    parser.add_argument(
        '--media-path',
        help=(
            "Path to the folder containing media files relative to "
            "the current directory "
            "(defaults to a 'media' folder inside the source folder)"
        )
    )
    parser.add_argument(
        '--output-path',
        help="Destination path for the built HTML files (default: ./build)"
    )
    parser.add_argument(
        '--output-media-path',
        help=(
            "Where to put media files "
            "(defaults to a 'media' folder inside the output directory)"
        )
    )
    parser.add_argument(
        '--template-path',
        help=(
            "Path to an alternate wrapping template for the built HTML files "
            "(defaults to using the built-in template)"
        )
    )
    parser.add_argument(
        '--site-root',
        help=(
            "A URL path to the root of the site, for use in the 'home' "
            "link in the template (defaults to none)"
        )
    )
    parser.add_argument(
        '--media-url',
        help=(
            "Override prefix for linking to media inside the built HTML files "
            "(defaults to using relative paths, e.g.: ../media)"
        )
    )
    parser.add_argument(
        '--tag-manager-code',
        help=(
            "If you supply a tag manager code, the default template will "
            "render Google tag manager snippets into the built HTML."
        )
    )
    parser.add_argument(
        '--force',
        action="store_true",
        help=("Rebuild all files (assume all files have changed)")
    )
    parser.add_argument(
        '--build-version-branches',
        action='store_true',
        help=(
            "Build each branch mentioned in the `versions` file into a "
            "subfolder"
        )
    )
    parser.add_argument(
        '--search-url',
        help=(
            "The URL endpoint for performing searches from the header. "
            "The header search field will only be included if this is "
            "provided."
        )
    )
    parser.add_argument(
        '--search-placeholder',
        help=(
            "Placeholder text for including in the header search field. "
            "Default: 'Search documentation'."
        )
    )
    parser.add_argument(
        '--search-domain',
        dest='search_domains',
        action='append',
        help=(
            "Pass this 'domain' query parameter along with the search "
            "string when performing searches."
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
        '--quiet',
        action='store_true',
        help="Suppress output"
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help="Show the currently installed version of documentation-builder."
    )

    arguments = vars(parser.parse_args(arguments))

    if arguments['version']:
        print(
            pkg_resources.get_distribution(
                "ubuntudesign.documentation_builder"
            ).version
        )
        sys.exit()
    else:
        del arguments['version']

    # Return only defined arguments
    return {name: value for name, value in arguments.items() if value}


def main(system_arguments):
    """
    The starting point for the documentation-parser.
    Intended to be run through the command-line.
    """

    arguments = parse_arguments(system_arguments)
    Builder(**arguments)


if __name__ == "__main__":
    main(sys.argv[1:])
