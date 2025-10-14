# Obelisk-py Contribution and Development Guide

## Technical setup

This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies,
Python versions and deployments.
As a result, all metadata and dependencies are defined in the `pyproject.toml` file.
`uv` also automatically installs the dev dependencies, so no special handling is needed.

## Docs

Docs are in RST format under the `docs` folder.
Autodoc and autosummary are used to turn docblocks into documentation.
The online variant follows the main branch.

The build command boils down to the following:
```sh
uv run sphinx-build -M html docs/source/ docs/build/
```

We recommend running `python -m http.server` in the docs output folder to easily view the resulting docs during development.

## Checks and tests

We ship a ruff linting and format config in the pyproject,
as well as a mypy typing setup.
All three of these are ran in CI and, if enabled, in a pre-commit hook.
Be careful to not accidentally break our Python version tolerance.
The hooks can be enabled on UNIX-like systems by setting `git config core.hooksPath hooks/` in the root of this repository.

You may run the full checks as follows:
```sh
uv run ruff format --check
uv run ruff check
uv run mypy
```

We expect new code to contain as much docblocks as possible and type annotations.
User-facing API _must_ have type annotations.

Additionally, the `src/tests` folder contains basic testing,
which can be ran easily ran using `uv run pytest`.

It is recommended to at least add basic "can I initialize" tests for new code.

## Workflows

Our GitHub Actions setup consists of three workflows.
The CI workflow runs on any PR or push to main,
and runs the above mentioned checks and tests.

Format, lint and type checking is ran on Linux, for several supported Python versions.
The test suite is ran on MacOS, Linux and Windows, matrixed for the same set of Python versions.
No code gets merged that breaks this lint.

The sphinx workflow builds docs from main and deploys to GitHub Pages.
Pypi publishing is handled using PyPi Trusted Publishing using the pypi workflow on tag creation.

## Governance and conduct

This project is intended for and maintained by researchers of [PreDiCT](https://predict.idlab.ugent.be/).
Community contributions and bug reports are welcome, but subject to review and prioritisation by PreDiCT.

Obelisk-py is not directly maintained or supported by the Obelisk team.

Please behave in the official channels as you would in a professional research setting.
