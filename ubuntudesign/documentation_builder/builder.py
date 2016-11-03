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
    set_active_navigation_items,
    write_html
)


# Defaults
default_template = path.join(
    path.dirname(__file__),
    'resources',
    'template.html'
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
        force=False,
        build_version_branches=False,
        template_path=default_template,
        site_root=None,
        media_url=None,
        no_link_extensions=False,
        no_cleanup=False,
        quiet=False,
        out=sys.stdout,
        err=sys.stderr,
    ):
        # Properties
        self.quiet = quiet
        self._out = out
        self._err = err

        # Defaults
        source_path = path.normpath(path.join(base_directory, source_folder))
        media_path = media_path or path.join(source_path, 'media')
        output_media_path = output_media_path or path.join(
            output_path, 'media'
        )

        parser = markdown.Markdown(extensions=markdown_extensions)

        with open(template_path, encoding="utf-8") as template_file:
            template = Template(template_file.read())

        branch_paths = prepare_branches(
            base_directory,
            output_path,
            build_version_branches
        )

        for (branch_directory, branch_output) in branch_paths:
            branch_source = path.normpath(
                path.join(branch_directory, source_folder)
            )

            if not path.isfile(path.join(branch_source, 'metadata.yaml')):
                self._fail(
                    (
                        "No metadata.yaml found in the source folder.\n\n"
                        "Documentation repository source folders should "
                        "contain a ./metadata.yaml file.\n\n"
                        "See "
                        "https://github.com/canonicalltd/documentation-builder"
                        " for instructions.\n"
                    )
                )

            metadata_items = find_metadata(branch_source)

            # Decide which files need changing
            files = find_files(branch_source, branch_output, metadata_items)

            new_files = files[0]
            if force:
                modified_files = files[1] + files[2]
                unmodified_files = []
            else:
                modified_files = files[1]
                unmodified_files = files[2]
            uppercase_files = files[3]
            parse_files = new_files + modified_files

            if uppercase_files:
                self._print(
                    'Skipping uppercase files:\n- {}'.format(
                        '\n- '.join(uppercase_files)
                    )
                )
            if unmodified_files:
                self._print(
                    'Skipping unmodified files:\n- {}'.format(
                        '\n- '.join(unmodified_files)
                    )
                )

            built_files = []

            # Create output files
            for filepath in parse_files:
                relative_filepath = path.relpath(filepath, branch_source)
                file_directory = path.normpath(path.dirname(filepath))
                relative_directory = path.dirname(relative_filepath)

                metadata = compile_metadata(
                    metadata_items,
                    path.relpath(file_directory, branch_source)
                )
                metadata['site_root'] = site_root

                navigation = metadata.get('navigation')

                # Breadcrumbs
                if navigation:
                    metadata['breadcrumbs'] = set_active_navigation_items(
                        path.basename(filepath),
                        navigation
                    )

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

                html = replace_internal_links(
                    html,
                    extensions=(not no_link_extensions)
                )

                output_filepath = path.join(branch_output, relative_filepath)

                built_filepath = write_html(html, output_filepath)
                built_files.append(built_filepath)

        if built_files:
            self._print("Built:\n- {}".format('\n- '.join(built_files)))

        try:
            if copy_media(media_path, output_media_path):
                self._print(
                    "Copied {} to {}".format(media_path, output_media_path)
                )
        except EnvironmentError as copy_error:
            self._warn("Copying media failed: " + str(copy_error))

    def _print(self, message, channel=None):
        if not self.quiet:
            print(message, file=channel or self._out)

    def _warn(self, message):
        self._print("Warning: " + message, channel=self._err)

    def _fail(self, message):
        self._print("Error: " + message, channel=self._err)
        sys.exit(1)
