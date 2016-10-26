# Core modules
import re
from collections import Mapping
from os import path

# Local modules
from .utilities import mergetree, relativize, replace_links


def replace_media_links(
    html,
    old_path,
    new_path,
    context_directory='.'
):
    """
    Replace links to media with the new media location.
    Do this intelligently relative to the current directory of the file.
    """

    if old_path:
        if not path.isabs(old_path):
            old_path = path.relpath(old_path, context_directory)
        if not path.isabs(new_path):
            new_path = path.relpath(new_path, context_directory)

        html = replace_links(html, old_path, new_path)

    return html


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


def copy_media(media_path, output_media_path):
    """
    Copy media files from source_media_path to output_media_path
    """

    media_paths_match = path.relpath(
        media_path, output_media_path
    ) == '.'

    if not media_paths_match:
        mergetree(media_path, output_media_path)

        return True
