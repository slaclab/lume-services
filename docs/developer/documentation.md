# Documentation

Documentation for this project


## MkDocs
For documentation, we use [mkdocs](https://www.mkdocs.org/) to automatically generate our [GitHub documentation](https://jacquelinegarrahan.github.io/lume-services/) using the mkdocs.yml packaged in the root of the project directory.


`docs/api` contains the API documentation compiled from docstrings.

This doesn't happen automatically
-add page to hierarchy in mkdocs.yml

Auto generated diagrams:
- schema
- class diagrams...
-

### Plugins

We use the [`mkdocstrings`](https://mkdocstrings.github.io/) plugin for building the [API documentation]((../api). This introspects the docstrings on each of our python objects and assembles documentation based on the typed arguments, attributes, returns, etc.


## Badges
This repo uses https://shields.io/ for creating badges packaged with the documentation. Most of these are automatically inferred from repo metadata with the exception of the coverage badge. The coverage badge is generated in the `coverage` job in the `.github/workflows/test.yml` workflow. The coverage job formats the coverage report an creates a comment on the commit being tested. That comment is then used by the last step to dynamically format the badge by storing a json representation of badge data in a Github [gist](https://gist.githubusercontent.com/jacquelinegarrahan/61dce43449fc0509f34520fd7efc41b1/raw/slaclab-lume-services-coverage.json).

In order for this to happen, the repository secret `PYTEST_COVERAGE_COMMENT` points to a personal auth token. The maintainer can create a new gist and update the `PYTEST_COVERAGE_COMMENT` to a new [auth string](https://github.com/settings/tokens).

<br>
The comment is created by the subaction: https://github.com/marketplace/actions/python-coverage-comment
<br>
The dynamic badge is formatted by the subaction:  https://github.com/marketplace/actions/dynamic-badges
