# discolinks

[![Build Status][build_status_badge]][build_status_link]
[![PyPI version][pypi_badge]][pypi_link]

Discolinks looks for broken links on a website.

Features:

- Starts on one page and recursively finds the other reachable pages on the website.
- Asynchronous: Maximum number of parallel requests is configurable.
- JSON output available: Useful for testing and scripting.

## Getting Started

```bash
$ discolinks --url https://example.net
📂 Results: 13 links (10 ok, 3 failed)
├── 📄 https://example.net/foo
│   ├── 🔗 /bad_absolute_href: 302 → 404
│   └── 🔗 bad_relative_href: 404
└── 📄 https://example.net/bar
    └── 🔗 https://example.org/bad_external_href: Connection error
```

## Development

```bash
... # Activate virtualenv.
poetry install
make check
```

## Release

- Create a branch with a name like `release-1.2.3`.
- Update version in `src/discolinks/__version__.py`.
- Update version in `pyproject.toml`.
- Update changelog.
- Open a pull request and get it merged.
- Tag the release `git tag --message 'Version 1.2.3' 1.2.3`
- Push tags: `git push --tags`

[build_status_badge]: https://github.com/bbc2/discolinks/actions/workflows/main.yml/badge.svg
[build_status_link]: https://github.com/bbc2/discolinks/actions/workflows/main.yml
[pypi_badge]: https://img.shields.io/pypi/v/discolinks
[pypi_link]: https://pypi.org/project/discolinks/
