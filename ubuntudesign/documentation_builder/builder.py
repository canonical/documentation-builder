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
from markdown.extensions.codehilite import CodeHiliteExtension
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
    prepare_version_branches,
    set_active_navigation_items,
    version_paths,
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
    CodeHiliteExtension(),
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
        search_url=None,
        search_placeholder='Search documentation',
        search_domains=[],
        site_root=None,
        media_url=None,
        tag_manager_code=None,
        no_link_extensions=False,
        no_cleanup=False,
        quiet=False,
        out=sys.stdout,
        err=sys.stderr,
    ):
        # Defaults
        source_path = path.normpath(path.join(base_directory, source_folder))

        # Properties
        self.quiet = quiet
        self.force = force
        self.site_root = site_root
        self.source_folder = source_folder
        self.base_directory = base_directory
        self.media_url = media_url
        self.tag_manager_code = tag_manager_code
        self.search_url = search_url
        self.search_placeholder = search_placeholder
        self.search_domains = search_domains
        self.no_link_extensions = no_link_extensions
        self.parser = markdown.Markdown(extensions=markdown_extensions)
        with open(template_path, encoding="utf-8") as template_file:
            self.template = Template(template_file.read())
        self.output_media_path = output_media_path or path.join(
            output_path, 'media'
        )
        self.media_path = media_path or path.join(source_path, 'media')
        self._out = out
        self._err = err

        built_files = []

        if not path.isdir(base_directory):
            raise FileNotFoundError(
                'Base directory not found: {}'.format(base_directory)
            )

        if build_version_branches:
            version_branches = prepare_version_branches(
                base_directory,
                output_path
            )

            for version_name, version_info in version_branches.items():
                built_files = self.build_branch(
                    version_info['base_directory'],
                    version_info['output_path'],
                    version_branches
                )
                if built_files:
                    self._print("Built:\n- {}".format(
                        '\n- '.join(built_files))
                    )
        else:
            built_files = self.build_branch(base_directory, output_path)

            if built_files:
                self._print("Built:\n- {}".format('\n- '.join(built_files)))

        if path.isdir(self.media_path):
            copy_media(self.media_path, self.output_media_path)
            self._print(
                "Copied {} to {}".format(
                    self.media_path,
                    self.output_media_path
                )
            )
        else:
            self._note(
                "No folder found at '{}' - not copying media".format(
                    self.media_path
                )
            )

    def build_branch(
        self,
        branch_base,
        output_path,
        version_branches={},
        relative_build_directory='.'
    ):
        """
        Build an individual branch of documentation
        """

        source_path = path.normpath(
            path.join(branch_base, self.source_folder)
        )

        if not path.isfile(path.join(source_path, 'metadata.yaml')):
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

        metadata_items = find_metadata(source_path)

        # Decide which files need changing
        files = find_files(source_path, output_path, metadata_items)

        new_files = files[0]
        if self.force:
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
            relative_filepath = path.relpath(filepath, source_path)
            file_directory = path.normpath(path.dirname(filepath))
            relative_directory = path.dirname(relative_filepath)

            metadata = compile_metadata(
                metadata_items,
                path.relpath(file_directory, source_path)
            )
            metadata['site_root'] = self.site_root
            metadata['tag_manager_code'] = self.tag_manager_code
            metadata['search_url'] = self.search_url
            metadata['search_placeholder'] = self.search_placeholder
            metadata['search_domains'] = self.search_domains

            navigation = metadata.get('navigation')

            # Breadcrumbs
            if navigation:
                metadata['breadcrumbs'] = set_active_navigation_items(
                    path.basename(filepath),
                    navigation
                )

            if version_branches:
                metadata['versions'] = version_paths(
                    version_branches,
                    branch_base,
                    self.source_folder,
                    relative_filepath
                )

            html = parse_markdown(
                self.parser,
                self.template,
                filepath,
                metadata
            )

            relative_media_path = path.relpath(
                self.media_path,
                path.join(self.base_directory, self.source_folder)
            )
            relative_output_media_path = path.relpath(
                self.output_media_path,
                output_path
            )

            html = replace_media_links(
                html,
                old_path=relative_media_path,
                new_path=self.media_url or relative_output_media_path,
                context_directory=relative_directory
            )

            html = replace_internal_links(
                html,
                extensions=(not self.no_link_extensions)
            )

            output_filepath = path.join(output_path, relative_filepath)

            built_filepath = write_html(html, output_filepath)
            built_files.append(built_filepath)

        return built_files

    def _print(self, message, channel=None):
        if not self.quiet:
            print(message, file=channel or self._out)

    def _note(self, message):
        self._print("Notice: " + message, channel=self._err)

    def _fail(self, message):
        self._print("Error: " + message, channel=self._err)
        sys.exit(1)
