---
title: "How to structure documentation repositories"
---

# How to structure documentation repositories

The documentation builder can work with various different file structures.

## Minimum requirements

The minimum that the builder requires to do anything useful is a single
`metadata.yaml` file, and a single markdown file:

``` bash
├── index.md
└── metadata.yaml  # Top-level site_title & navigation
```

Running `documentation-builder` here will create a single file at
`build/index.html`.

## Recommended documentation repository structure

This is the recommended standard structure:

- Keep all documentation inside language folders, for building in multi-lingual
  support in the future
- Keep site-wide settings in a top-level `metadata.yaml`, but define navigation
  on a per-language level with `metadata.yaml` files inside each language directory:

``` bash
├── media              # The media directory
|   ├── welcome.png    # An image
├── en                 # Language folder
│   ├── index.md       # English language documentation
│   └── metadata.yaml  # Define navigation for English documentation
├── fr                 # Language folder
│   ├── index.md       # French language documentation
│   └── metadata.yaml  # Define navigation for French documentation
└── metadata.yaml      # Top-level settings (site_title etc.)
```

## Internal links

In both the markdown files and the `metadata.yaml` files, links should be
written as *relative links* to the file *as it exists in the source repository*.
This means the source documentation remains internally consistent. E.g.:

``` html
<!-- en/index.md -->

![welcome image](../media/welcome.png)

We also have [../fr/index.md](French documentation).
```

``` yaml
# en/metadata.yaml
navigation:
  - title: Introduction
    location: index.md
  - title: French documentation
    location: ../fr/index.md
```

These links will then be rewritten so they continue to work in the built
documentation.

## Metadata syntax

The metadata is written in YAML format, which will be passed through as template
variables when parsing the markdown.

### Cascading metadata

The builder will look for `metadata.yaml` files relative to the current
markdown file being built by first looking in the same directory as the file
and then traversing up the file tree until it reaches the documentation project
root.

Top-level keys in `metadata.yaml` files closer to the markdown file will take
precedence over files further away. This way the top-level `./metadata.yaml`
settings can always be overridden within subfolders, e.g. with `./en/metadata.yaml`.

Additionally, the builder will look for [YAML frontmatter](https://jekyllrb.com/docs/frontmatter/)
in each file, which will override any keys from `metadata.yaml` files.

### Config options

You can define whatever metadata you like, and then make use of it by
providing your own template to the builder with `--template-path`.

However, in the [default template](https://github.com/CanonicalLtd/documentation-builder/blob/master/ubuntudesign/documentation_builder/resources/template.html), the following options are defined:

### Top level config options

- `site_title`: A title for the site, to be used in both the META title
  in the <head> and the <header> at the top of the page
- `site_logo_url`: An absolute URL to a logo image for displaying in the
  <header> at the top of the page.
- `site_root`: The URL path (e.g. '/') to link to when clicking the site title.
  Can also be specified with the `--site-root` option.
- `navigation`: A list defining all navigation options for the site.

### Page-level config options

You can define [YAML frontmatter](https://jekyllrb.com/docs/frontmatter/)
in individual pages as follows:

``` markdown
---
title: "Some metadata"   # Define the <title> element in the HTML <head>
table_of_contents: True  # Enable the table of contents for this page
---

# title

Hello world
```

### Navigation

The `navigation` node needs to be in the following format:

``` yaml
navigation:
  - title: Introduction
    location: en/index.md

  - title: Section one
    children:
      - title: Section intro
        location: en/one/intro.md

  - title: Section two
    children:
      - title: About MAAS
        location: en/index.md
      - title: About MAAS
        location: en/index.md
```

## Versions

Separate versions of the documentation should be kept in separate Git
branches. These branches should then be specified in a `versions` file in the
base of the repository, one branch name per line. E.g.:

``` bash
# ./versions
1.0
latest
```

All versions can then be built together with the `build-version-branches` flag:

``` bash
$ documentation-builder --build-version-branches
```

This will then build each version branch into its own sub-directory inside the
`build` folder:

``` bash
└── build                   # The build directory
    ├── 1.0                 # Branch directory
    |   └── en              # Folder from branch
    |       └── index.html  # File from branch
    └── latest
        └── en
            └── index.html
```
