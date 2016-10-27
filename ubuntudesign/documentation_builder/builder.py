# Core modules
import sys
from os import path

# Third party modules
import markdown
from jinja2 import Template
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.meta import MetaExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from mdx_callouts import makeExtension as CalloutsExtension
from mdx_anchors_away import AnchorsAwayExtension
from mdx_foldouts import makeExtension as FoldoutsExtension

# Local modules
from .operations import (
    compile_metadata,
    copy_media,
    find_files,
    find_metadata,
    replace_internal_links,
    replace_media_links,
    parse_markdown,
    prepare_branches,
    write_html
)


# Defaults
default_template = path.join(
    path.dirname(__file__),
    'resources',
    'wrapper.jinja2'
)
markdown_extensions = [
    MetaExtension(),
    TableExtension(),
    FencedCodeExtension(),
    DefListExtension(),
    AttrListExtension(),
    TocExtension(marker='', baselevel=1),
    CalloutsExtension(),
    AnchorsAwayExtension(),
    FoldoutsExtension()
]


class Builder():
    def __init__(
        self,
        base_directory='.',
        source_folder='.',
        output_path='build',
        media_path=None,
        output_media_path=None,
        build_version_branches=False,
        template_path=default_template,
        site_root=None,
        media_url=None,
        no_link_extensions=False,
        no_cleanup=False,
        quiet=False
    ):
        self.quiet = quiet
        media_path = media_path or path.join(base_directory, 'media')
        output_media_path = output_media_path or path.join(
            output_path, 'media'
        )

        parser = markdown.Markdown(extensions=markdown_extensions)

        with open(template_path, encoding="utf-8") as template_file:
            template = Template(template_file.read())

        relative_media_path = None

        try:
            if copy_media(media_path, output_media_path):
                self._print(
                    "Copied {} to {}".format(media_path, output_media_path)
                )
        except EnvironmentError as copy_error:
            self._warn(str(copy_error))

        branch_paths = prepare_branches(
            base_directory,
            output_path,
            build_version_branches
        )

        for (branch_directory, branch_output) in branch_paths:
            source_path = path.join(branch_directory, source_folder)

            metadata_items = find_metadata(source_path)

            if not metadata_items:
                self._fail(
                    "\nNo metadata.yaml found, is this a repository "
                    "of documentation?\n"
                    "\n"
                    "See https://github.com/canonicalltd/documentation-builder"
                    " for instructions.\n",
                    file=sys.stderr
                )

            # Decide which files need changing
            files = find_files(source_path, branch_output, metadata_items)

            new_files = files[0]
            modified_files = files[1]
            unmodified_files = files[2]
            uppercase_files = files[3]
            skip_files = unmodified_files + uppercase_files
            parse_files = new_files + modified_files

            self._print(
                'Skipping: {}\nParsing: {}'.format(
                    '\n- '.join(skip_files),
                    '\n- '.join(parse_files)
                )
            )

            # Create output files
            for filepath in parse_files:
                relative_filepath = path.relpath(filepath, source_path)
                file_directory = path.dirname(filepath)
                relative_directory = path.dirname(relative_filepath)

                metadata = compile_metadata(
                    metadata_items,
                    path.relpath(file_directory, source_path)
                )
                metadata['site_root'] = site_root

                html = parse_markdown(parser, template, filepath, metadata)

                relative_media_path = path.relpath(
                    media_path,
                    path.join(base_directory, source_folder)
                )
                relative_output_media_path = path.relpath(
                    output_media_path,
                    branch_output
                )

                html = replace_media_links(
                    html,
                    relative_media_path,
                    media_url or relative_output_media_path,
                    relative_directory
                )

                html = replace_internal_links(html)

                output_filepath = path.join(branch_output, relative_filepath)

                self._print("Writing: {}".format(output_filepath))
                write_html(html, output_filepath)

    def _print(self, message, channel=sys.stdout):
        if not self.quiet:
            print(message, file=channel)

    def _warn(self, message):
        self._print("Warning: " + message, channel=sys.stderr)

    def _fail(self, message):
        self._print("Error: " + message, channel=sys.stderr)
        sys.exit(1)
