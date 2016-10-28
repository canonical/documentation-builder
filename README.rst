Ubuntu documentation builder
============================

.. figure:: https://travis-ci.org/CanonicalLtd/documentation-builder.svg?branch=master
   :alt: build status
   :title: status of tests
   :target: https://travis-ci.org/CanonicalLtd/documentation-builder

.. figure:: https://coveralls.io/repos/github/CanonicalLtd/documentation-builder/badge.svg?branch=master
   :alt: code coverage
   :title: code coverage
   :target: https://coveralls.io/github/CanonicalLtd/documentation-builder


A tool for building a set of documentation files in HTML format, from a
remote git repository containing markdown files.

Installation
------------

.. code:: bash

    snap install documentation-builder

For more information see `the documentation <docs/en/index.md>`__.

Tests
----

To run tests:

.. code:: bash

    ./setup.py test
