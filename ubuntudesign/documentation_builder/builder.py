# Core modules
import re
import sys
import tempfile
from collections import Mapping, OrderedDict
from copy import deepcopy
from glob import iglob
from os import makedirs, path
from shutil import rmtree

# Third party modules
import frontmatter
import markdown
import yaml
from git import Repo
from jinja2 import Template
from yaml.scanner import ScannerError
from yaml.parser import ParserError

# Local modules
from .utilities import mergetree

# Configuration
# ==
default_title = 'Juju Documentation'
markdown_extensions = [
    'markdown.extensions.meta',
    'markdown.extensions.tables',
    'markdown.extensions.fenced_code',
    'markdown.extensions.def_list',
    'markdown.extensions.attr_list',
    'markdown.extensions.toc',
    'callouts',
    'anchors_away',
    'foldouts'
]
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

    markdown_parser = markdown.Markdown(extensions=markdown_extensions)

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
    Update a relative path considering a new context
    """

    if location.startswith('/'):
        abs_location = location.rstrip('/')
    else:
        abs_location = '/' + path.join(original_base_path, location).strip('/')
    abs_dirpath = '/' + new_base_path

    return path.relpath(abs_location, abs_dirpath)


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
        media_url,
        no_link_extensions,
        ignore_files
    ):
        self.source_path = source_path
        self.source_media_path = source_media_path
        self.output_path = output_path
        self.output_media_path = output_media_path
        self.template = template
        self.media_url = media_url
        self.no_link_extensions = no_link_extensions
        self.ignore_files = ignore_files

    def build(self):
        """
        Entrypoint: Build documentation folder
        """

        self._load_contexts()
        self._copy_media()
        self._build_files()

    def _load_contexts(self):
        """
        Find and load context files
        """

        self.contexts = OrderedDict()

        context_match = '{root}/**/context.yaml'.format(root=self.source_path)

        for context_filepath in iglob(context_match, recursive=True):
            with open(context_filepath) as context_file:
                context_localpath = path.relpath(
                    context_filepath,
                    self.source_path
                )
                self.contexts[path.dirname(context_localpath)] = yaml.load(
                    context_file.read()
                )

    def _build_files(self):
        """
        Given a folder of markdown files,
        parse all files into a new folder of HTML files
        """

        for filepath in iglob(
            path.join(self.source_path, '**/*.md'),
            recursive=True
        ):
            if path.basename(filepath) in self.ignore_files:
                print("Ignored {}".format(filepath))
            else:
                self._build_file(filepath)

    def _copy_media(self):
        """
        Copy media files from source_media_path to output_media_path
        """

        if path.isdir(self.source_media_path):
            media_paths_match = path.relpath(
                self.source_media_path, self.output_media_path
            ) == '.'

            if not media_paths_match:
                mergetree(self.source_media_path, self.output_media_path)
                print(
                    "Copied {} to {}".format(
                        self.source_media_path, self.output_media_path
                    )
                )
        else:
            print(
                "Warning: Media directory not found at {}.".format(
                    self.source_media_path
                ),
                file=sys.stderr
            )

    def _build_file(self, source_filepath):
        """
        Create an HTML file for a documentation page from a path to the
        corresponding Markdown file
        """

        # Decide output filepath
        local_path = path.relpath(source_filepath, self.source_path)

        output_filepath = re.sub(
            r'\.md$',
            '.html',
            path.join(self.output_path, local_path)
        )

        # Get HTML
        html_document = self._build_html(source_filepath, output_filepath)

        # Write output to file
        self._write_file(html_document, output_filepath)

    def _build_html(self, source_filepath, output_filepath):
        """
        Parse markdown file with template to output full HTML markup
        """

        # Parse the markdown
        (html_content, metadata) = parse_markdown(source_filepath)

        # Build document from template
        local_context = self._build_context(source_filepath, output_filepath)
        local_context.update(metadata)
        local_context['content'] = html_content
        html_document = self.template.render(local_context)

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

    def _build_context(self, source_filepath, output_filepath):
        """
        Construct the template context for an individual page,
        by finding and merging all context.yaml files from this folder to the
        documentation root
        """

        local_context = {}
        source_dirpath = path.dirname(source_filepath)
        local_filepath = path.relpath(source_filepath, self.source_path)
        local_dirpath = path.dirname(local_filepath)

        for context_dirpath, content in self.contexts.items():
            if source_dirpath.startswith(context_dirpath):
                context = deepcopy(content)
                context = relativize_paths(
                    context,
                    context_dirpath,
                    local_dirpath
                )
                local_context.update(context)

        return local_context

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

        print("Created {output_filepath}".format(**locals()))


def build(
    repository=None,
    branch=None,
    source_path='.',
    source_media_dir='media',
    output_path='build',
    output_media_path='build/media',
    template_path=None,
    media_url=None,
    no_link_extensions=False,
    no_cleanup=False,
    ignore_files=['README.md']
):
    with open(template_path or default_template) as template_file:
        template = Template(template_file.read())

    if repository:
        repo_dir = tempfile.mkdtemp()
        print("Cloning {repository} into {repo_dir}".format(**locals()))
        if branch:
            Repo.clone_from(repository, repo_dir, branch=branch)
        else:
            Repo.clone_from(repository, repo_dir)

        source_path = path.join(repo_dir, source_path)

    try:
        builder = Builder(
            source_path=source_path,
            source_media_path=path.join(source_path, source_media_dir),
            output_path=output_path,
            output_media_path=output_media_path,
            template=template,
            media_url=media_url,
            no_link_extensions=no_link_extensions,
            ignore_files=ignore_files
        )
        builder.build()

    finally:
        if repository and not no_cleanup:
            print("Cleaning up {repo_dir}".format(**locals()))
            rmtree(repo_dir)
