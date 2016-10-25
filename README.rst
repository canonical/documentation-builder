Ubuntu documentation builder
============================

A tool for building a set of documentation files in HTML format, from a
remote git repository containing markdown files.

Installation
------------

.. code:: bash

    snap install documentation-builder

Usage
-----

To build a local folder of markdown files in the appropriate format into HTML files:

.. code:: bash

    $ documentation-builder  # Build markdown documentation from the current directory

Optional arguments:

.. code:: bash

    $ documentation-builder \
        --base-directory {dirpath}        `# Path to the base folder for the documentation repository`
        --source-folder {dirpath}         `# Path to the folder containing markdown files inside the base directory (default: .)`
        --media-path {dirpath}            `# Path to the folder containing media files (default: ./media)`
        --site-root {local-url-path}      `# A URL path to the root of the site, for use in the 'home' link in the template`
        --output-path {dirpath}           `# Destination path for the built HTML files (default: ./build)`
        --output-media-path {dirpath}     `# Where to put media files (default: ./build/media)`
        --template-path {filepath}        `# Path to an alternate wrapping template for the built HTML files`
        --media-url {prefix}              `# Prefix for linking to media inside the built HTML files (default: Relative path to built media location, e.g.: ../media)`
        --no-link-extensions              `# Don't include '.html' extension in internal links`
        --no-cleanup                      `# Don't clean up temporary directory after cloning repository`
        --quiet                           `# Suppress output`
