---
title: "Getting started with documentation-builder"
---

Getting started with documentation-builder
===

documentation-builder is a tool for building a set of HTML documentation
from a remote git repository containing markdown files.

Installation
---

``` bash
snap install documentation-builder
```

Usage
---

To build a local folder of markdown files in the appropriate format into
HTML files:

``` bash
$ documentation-builder  # Build markdown documentation from the current directory
```

Optional arguments:

``` bash
$ documentation-builder \
    --base-directory {dirpath}        `# Path to the base folder for the documentation repository`
    --source-folder {dirpath}         `# Path to the folder containing markdown files inside the base directory (default: .)`
    --media-path {dirpath}            `# Path to the folder containing media files (default: ./media)`
    --output-path {dirpath}           `# Destination path for the built HTML files (default: ./build)`
    --output-media-path {dirpath}     `# Where to put media files (default: ./build/media)`
    --template-path {filepath}        `# Path to an alternate wrapping template for the built HTML files`
    --site-root {root_path}           `# A URL path to the root of the site, for use in the 'home' link in the template (defaults to none)`
    --media-url {prefix}              `# Prefix for linking to media inside the built HTML files (default: Relative path to built media location, e.g.: ../media)`
    --tag-manager-code {code}         `# If you supply a tag manager code, the default template will render Google tag manager snippets into the built HTML.`
    --force                           `# Rebuild all files (assume all files have changed).`
    --build-version-branches          `# Build each branch mentioned in the `versions` file into a subfolder`
    --no-link-extensions              `# Don't include '.html' extension in internal links`
    --no-cleanup                      `# Don't clean up temporary directory after cloning repository`
    --quiet                           `# Suppress output`
    --version                         `# Show the currently installed version of documentation-builder`
```
