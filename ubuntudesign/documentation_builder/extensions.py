"""
Custom markdown extensions for the documentation builder
"""

# Core
from __future__ import absolute_import
from __future__ import unicode_literals
import re
import jinja2

# Local
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree


class NotificationsExtension(Extension):
    """
    # Notifications extension for Python Markdown

    This provides the ability to create [vanilla notifications][1].

    Usage:

        !!! Note:
            Things are reasonable

        !!! Warning "":
            I have no title

        !!! Positive "Awesome":
            Everything is now wonderful

    Will generate the following markup:

        <div class="p-notification">
          <p class="p-notification__response">
            <span class="p-notification__status">Note:</span>
            <span class="p-notification__line">Things are reasonable</span>
          </p>
        </div>

        <div class="p-notification--caution">
          <p class="p-notification__response">
            <span class="p-notification__line">I have no title</span>
          </p>
        </div>

        <div class="p-notification--positive">
          <p class="p-notification__response">
            <span class="p-notification__status">Awesome:</span>
            <span class="p-notification__line">
                Everything is now wonderful
            </span>
          </p>
        </div>

    This builds on Python Markdown's existing [admonition extension][2].

    [1]: https://docs.vanillaframework.io/en/patterns/notification
    [2]: https://pythonhosted.org/Markdown/extensions/admonition.html
    """

    def extendMarkdown(self, md, md_globals):
        """ Add Notifications to Markdown instance. """
        md.registerExtension(self)

        md.parser.blockprocessors.add(
            'notifications',
            NotificationsProcessor(md.parser),
            '_begin'
        )


class NotificationsProcessor(BlockProcessor):

    line_match = re.compile(r'(?:^|\n)!!!\ ?([\w\-]+)(?:\ "(.*?)")?')

    def test(self, parent, block):
        sibling = self.lastChild(parent)

        return (
            self.line_match.search(block) or
            (
                block.startswith(' ' * self.tab_length) and
                sibling is not None and
                sibling.get('class', '').startswith('p-notification')
            )
        )

    def run(self, parent, blocks):
        sibling = self.lastChild(parent)
        block = blocks.pop(0)
        match = self.line_match.search(block)

        if match:
            block = block[match.end() + 1:]  # removes the first line

        block, theRest = self.detab(block)
        contents = block.replace('\n', ' ').replace('\r', '').strip()

        if match:
            template = jinja2.Template(
                '<div class="{{ class }}">' +
                '  <p class="p-notification__response">' +
                '    {% if title %}' +
                '      <span class="p-notification__status">' +
                '        {{ title }}:' +
                '      </span>' +
                '    {% endif %}' +
                '    <span class="p-notification__line">{{body}}</span>' +
                '  </p>' +
                '</div>'
            )
            notification_type, title = self.get_type_and_title(match)

            type_classes = {
                'warning': 'p-notification--caution',
                'positive': 'p-notification--positive',
                'negative': 'p-notification--negative',
                'information': 'p-notification--information',
            }

            markup = template.render(
                {
                    'class': type_classes.get(
                        notification_type,
                        'p-notification'
                    ),
                    'title': title,
                    'body': contents
                }
            )

            parent.append(etree.fromstring(markup))
        else:
            response_paragraph = sibling.find(
                "p[@class='p-notification__response']"
            )

            line_element = etree.fromstring(
                '<span class="p-notification__line">' +
                contents +
                '</span>'
            )

            response_paragraph.append(line_element)

    def get_type_and_title(self, match):
        notification_type, title = match.group(1).lower(), match.group(2)
        if title is None:
            # no title was provided, use the capitalized classname as title
            # e.g.: `!!! note` will render
            # `<span class="p-notification__status">Note</span>`
            title = notification_type.capitalize()
        elif title == '':
            # an explicit blank title should not be rendered
            # e.g.: `!!! warning ""` will *not* render the
            # `p-notification__status` title `span`
            title = None
        return notification_type, title
