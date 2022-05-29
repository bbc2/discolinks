# discolinks

This looks for broken links on a website.

Features:

- Starts on one page and recursively finds the other reachable pages on the website.
- Asynchronous: Maximum number of parallel requests is configurable.
- JSON output available: Useful for use in scripts.

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
