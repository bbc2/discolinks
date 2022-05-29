# discolinks

[![Build Status][build_status_badge]][build_status_link]

Discolinks looks for broken links on a website.

Features:

- Starts on one page and recursively finds the other reachable pages on the website.
- Asynchronous: Maximum number of parallel requests is configurable.
- JSON output available: Useful for testing and scripting.

## Getting Started

```bash
$ discolinks --url https://example.net
https://example.net/foo
  status code: 404
  origins:
    https://example.net: /foo
```

## Development

```bash
... # Activate virtualenv.
poetry install
make check
```

[build_status_badge]: https://github.com/bbc2/discolinks/actions/workflows/main.yml/badge.svg
[build_status_link]: https://github.com/bbc2/discolinks/actions/workflows/main.yml
