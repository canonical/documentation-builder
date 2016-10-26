# Core modules
import re
import sys
import tempfile
from collections import Mapping, OrderedDict
from copy import deepcopy
from glob import glob, iglob
from os import makedirs, path
from shutil import rmtree

# Third party modules
import frontmatter
import yaml
from bs4 import BeautifulSoup
from git import Repo
from jinja2 import Template

# Local modules
from .utilities import mergetree

# Markdown and plugins
import markdown
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.meta import MetaExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from mdx_callouts import makeExtension as CalloutsExtension
from mdx_anchors_away import AnchorsAwayExtension
from mdx_foldouts import makeExtension as FoldoutsExtension
from yaml.scanner import ScannerError
from yaml.parser import ParserError


# Configuration
# ==
default_title = 'Juju Documentation'
markdown_extensions = [
    MetaExtension(),
    TableExtension(),
    FencedCodeExtension(),
    DefListExtension(),
    AttrListExtension(),
    TocExtension(marker='', baselevel=1),
    CalloutsExtension(),
    AnchorsAwayExtension(),
    FoldoutsExtension(),
]

markdown_parser = markdown.Markdown(extensions=markdown_extensions)

default_template = path.join(
    path.dirname(__file__),
    'resources',
    'wrapper.jinja2'
)


def parse_markdown(filepath):
    """
    Parse an individual markdown file to HTML, also returning
    the meta title
    """

    markdown_parser.reset()

    metadata = {}

    # Try to extract frontmatter metadata
    try:
        file_parts = frontmatter.load(filepath)
        metadata = file_parts.metadata
        markdown_content = file_parts.content
    except (ScannerError, ParserError):
        """
        If there's a parsererror, it may be because there is no YAML
        frontmatter, so it got confused. Let's just continue.
        """

        with open(filepath) as markdown_file:
            markdown_content = markdown_file.read()

    html_content = markdown_parser.convert(markdown_content)

    # Now add on any multimarkdown-format metadata
    if hasattr(markdown_parser, 'Meta'):
        # Restructure markdown parser metadata to the same format as we expect
        markdown_meta = markdown_parser.Meta

        for name, value in markdown_meta.items():
            if type(value) == list and len(value) == 1:
                markdown_meta[name] = value[0]

        metadata.update(markdown_meta)

    if metadata.get('table_of_contents'):
        toc_soup = BeautifulSoup(markdown_parser.toc, 'html.parser')

        # Get title list item (<h1>)
        nav_item_strings = []

        # Only get <h2> items, to avoid getting crazy
        for item in toc_soup.select('.toc > ul > li > ul > li'):
            for child in item('ul'):
                child.extract()

            item['class'] = 'p-toc__item'

            nav_item_strings.append(str(item))

        metadata['toc_items'] = "\n".join(nav_item_strings)

    return (html_content, metadata)


def relativize_paths(item, original_base_path, new_base_path):
    """
    Recursively search a dictionary for items that look like local markdown
    locations, and replace them to be relative to local_dirpath instead
    """

    internal_link_match = r'^[^ "\']+.md(#|\?|$)'

    original_base_path = original_base_path.strip('/')
    new_base_path = new_base_path.strip('/')

    if isinstance(item, Mapping):
        for key, child in item.items():
            item[key] = relativize_paths(
                child,
                original_base_path,
                new_base_path
            )
    elif isinstance(item, list):
        for index, child in enumerate(item):
            item[index] = relativize_paths(
                child,
                original_base_path,
                new_base_path
            )
    elif isinstance(item, str) and re.match(internal_link_match, item):
        item = relativize(
            item,
            original_base_path,
            new_base_path
        )

    return item


def relativize(location, original_base_path, new_base_path):
    """
    Update a relative path for a new base location
    """

    if location.startswith('/'):
        abs_location = location.rstrip('/')
    else:
        abs_location = '/' + path.join(original_base_path, location).strip('/')
    abs_dirpath = '/' + new_base_path

    return path.relpath(abs_location, abs_dirpath)


def copy_media(source_path, output_path, quiet=False):
    """
    Copy media files from source_media_path to output_media_path
    """

    if not path.isdir(source_path):
        if not quiet:
            print(
                "Warning: Media directory not found at {}.".format(
                    source_path
                ),
                file=sys.stderr
            )
            return

    media_paths_match = path.relpath(
        source_path, output_path
    ) == '.'

    if not media_paths_match:
        mergetree(source_path, output_path)
        if not quiet:
            print(
                "Copied {} to {}".format(source_path, output_path)
            )


class Builder:
    """
    Parse a remote git repository of markdown files into HTML files in the
    specified build folder
    """

    internal_link_match = re.compile(r'\b([^ "\']+)\.md\b')

    def __init__(
        self,
        source_path,
        source_media_path,
        output_path,
        output_media_path,
        template,
        site_root,
        media_url,
        no_link_extensions,
        quiet
    ):
        self.source_path = path.normpath(source_path)
        self.source_media_path = path.normpath(source_media_path)
        self.output_path = path.normpath(output_path)
        self.output_media_path = path.normpath(output_media_path)
        self.template = template
        self.site_root = site_root
        self.media_url = media_url
        self.no_link_extensions = no_link_extensions
        self.quiet = quiet

    def build(self):
        """
        Entrypoint: Build documentation folder
        """

        self.metadata_trees = self._get_metadata()
        self._build_files()

    def _get_metadata(self):
        """
        Find and load metadata files
        """

        metadata_trees = OrderedDict()

        files_match = path.normpath(
            '{root}/**/metadata.yaml'.format(root=self.source_path)
        )
        files = glob(files_match, recursive=True)

        if not files:
            raise EnvironmentError('No metadata.yaml found')

        for filepath in files:
            with open(filepath) as metadata_file:
                metadata_trees[path.dirname(filepath)] = yaml.load(
                    metadata_file.read()
                )

        return metadata_trees

    def _build_files(self):
        """
        Given a folder of markdown files,
        parse all files into a new folder of HTML files
        """

        for filepath in iglob(
            path.normpath(path.join(self.source_path, '**/*.md')),
            recursive=True
        ):
            self._build_file(filepath)

    def _build_file(self, source_filepath):
        """
        Create an HTML file for a documentation page from a path to the
        corresponding Markdown file
        """

        # Ignore all uppercase filenames
        name = path.splitext(path.basename(source_filepath))[0]
        alphabet_name = re.sub(r'\W+', '', name)

        if alphabet_name.isupper():
            self._print("Skipping uppercase filename: {}".format(
                source_filepath
            ))
            return

        # Decide output filepath
        path_in_project = path.relpath(source_filepath, self.source_path)

        output_filepath = re.sub(
            r'\.md$',
            '.html',
            path.join(self.output_path, path_in_project)
        )

        # Skip if it's unmodified
        if path.exists(output_filepath) and (
            path.getmtime(output_filepath) > path.getmtime(source_filepath)
        ):
            self._print("Skipping unmodified file: {}".format(source_filepath))
            return

        # Get HTML
        html_document = self._build_html(source_filepath, output_filepath)

        # Write output to file
        self._write_file(html_document, output_filepath)

    def _build_html(self, source_filepath, output_filepath):
        """
        Parse markdown file with template to output full HTML markup
        """

        # Parse the markdown
        (html_content, local_metadata) = parse_markdown(source_filepath)

        # Build document from template
        metadata = self._build_metadata(source_filepath, output_filepath)
        metadata.update(local_metadata)
        metadata['content'] = html_content

        if self.site_root:
            metadata['site_root'] = self.site_root

        html_document = self.template.render(metadata)

        # Fixup internal references
        html_document = self._replace_media_links(
            html_document,
            source_filepath,
            output_filepath
        )
        html_document = self._replace_internal_links(
            html_document,
            source_filepath,
            output_filepath
        )

        return html_document

    def _build_metadata(self, source_filepath, output_filepath):
        """
        Construct the template metadata for an individual page,
        by finding and merging all metadata.yaml files from this folder to the
        documentation root
        """

        metadata = {}
        source_dirpath = path.dirname(source_filepath)
        path_in_project = path.relpath(source_filepath, self.source_path)
        dir_in_project = path.dirname(path_in_project)

        for metadata_tree_path, content in self.metadata_trees.items():
            if source_dirpath.startswith(metadata_tree_path):
                metadata_tree = deepcopy(content)
                metadata_tree = relativize_paths(
                    metadata_tree,
                    metadata_tree_path,
                    dir_in_project
                )
                metadata.update(metadata_tree)

        return metadata

    def _replace_internal_links(
        self,
        content,
        source_filepath,
        output_filepath
    ):
        """
        Swap out links to local .md files with the correct filenames
        """

        # Calculate relative path
        relative_media_path = path.relpath(
            self.output_media_path,
            path.dirname(output_filepath)
        )
        media_url = self.media_url or relative_media_path
        old_media_path = path.relpath(
            self.source_media_path,
            path.dirname(source_filepath)
        )

        # Replace internal document links
        if self.no_link_extensions:
            content = re.sub(
                self.internal_link_match,
                r'\1',
                content
            )
        else:
            content = re.sub(
                self.internal_link_match,
                r'\1.html',
                content
            )

        return content

    def _replace_media_links(
        self,
        content,
        source_filepath,
        output_filepath
    ):
        """
        Swap out old links to media with a path to the new location
        """

        original_media_path = path.relpath(
            self.source_media_path,
            path.dirname(source_filepath)
        )
        new_media_path = path.relpath(
            self.output_media_path,
            path.dirname(output_filepath)
        )
        media_url = self.media_url or new_media_path
        media_search = r'(?<=[\'"]){}(?=/)'.format(
            original_media_path.replace('.', '\.')
        )

        content = re.sub(media_search, media_url, content)

        return content

    def _write_file(self, html_document, output_filepath):
        """
        Create the output file with the HTML contents
        """

        # Check folder exists
        makedirs(path.dirname(output_filepath), exist_ok=True)

        with open(output_filepath, 'w') as output_file:
            output_file.write(html_document)

        self._print("Created {output_filepath}".format(**locals()))

    def _print(self, message, channel=sys.stdout):
        """
        Output a message unless quiet is on
        """

        if not self.quiet:
            print(message, file=channel)


def build(
    base_directory='.',
    source_folder='.',
    media_path='media',
    output_path='build',
    output_media_path='build/media',
    build_version_branches=False,
    template_path=None,
    site_root=None,
    media_url=None,
    no_link_extensions=False,
    no_cleanup=False,
    quiet=False
):
    with open(template_path or default_template) as template_file:
        template = Template(template_file.read())

    source_path = path.normpath(path.join(base_directory, source_folder))

    copy_media(media_path, output_media_path, quiet)

    if build_version_branches:
        versions_filepath = path.join(source_path, 'versions')

        if not path.exists(versions_filepath):
            print('Versions file not found at {}'.format(versions_filepath))
            sys.exit(1)

        with open(versions_filepath) as versions_file:
            lines = versions_file.read().splitlines()
            version_branches = list(filter(None, lines))

        for branch in version_branches:
            branch_dir = tempfile.mkdtemp()
            branch_source_path = path.join(branch_dir, source_folder)
            branch_output_path = path.join(output_path, branch)

            if not quiet:
                print('Cloning branch {} into {}'.format(branch, branch_dir))

            Repo.clone_from(base_directory, branch_dir, branch=branch)

            if not quiet:
                print(
                    'Building branch {} into {}'.format(
                        branch,
                        branch_output_path
                    )
                )

            try:
                builder = Builder(
                    source_path=branch_source_path,
                    source_media_path=media_path,
                    output_path=branch_output_path,
                    output_media_path=output_media_path,
                    template=template,
                    site_root=site_root,
                    media_url=media_url,
                    no_link_extensions=no_link_extensions,
                    quiet=quiet
                )
                builder.build()
            finally:
                if not no_cleanup:
                    print("Cleaning up {}".format(branch_dir))
                    rmtree(branch_dir)

    else:
        try:
            builder = Builder(
                source_path=source_path,
                source_media_path=media_path,
                output_path=output_path,
                output_media_path=output_media_path,
                template=template,
                site_root=site_root,
                media_url=media_url,
                no_link_extensions=no_link_extensions,
                quiet=quiet
            )
            builder.build()
        except:
            if not quiet:
                print(
                    "\nNo metadata.yaml found, is this a repository "
                    "of documentation?\n"
                    "\n"
                    "See https://github.com/canonicalltd/documentation-builder"
                    " for instructions.\n",
                    file=sys.stderr
                )
            sys.exit(1)
