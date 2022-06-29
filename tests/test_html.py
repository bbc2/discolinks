from typing import Sequence

import pytest

from discolinks.core import Url
from discolinks.html import get_hrefs, parse_href


@pytest.mark.parametrize(
    "body,expected",
    [
        ("<body></body>", []),
        ("""<a href="foo">""", ["foo"]),
        ("""<a href="foo#bar">""", ["foo#bar"]),
        ("""<a href="mailto:foo@example.net">""", ["mailto:foo@example.net"]),
    ],
)
def test_get_hrefs(body: str, expected: Sequence[str]):
    result = get_hrefs(body=body)

    assert list(result) == expected


@pytest.mark.parametrize(
    "href,base_url,expected",
    [
        (
            "",
            Url.from_str("http://example.net"),
            Url.from_str("http://example.net"),
        ),
        (
            "foo",
            Url.from_str("http://example.net"),
            Url.from_str("http://example.net/foo"),
        ),
        (
            "bar",
            Url.from_str("http://example.net/foo"),
            Url.from_str("http://example.net/bar"),
        ),
        (
            "bar",
            Url.from_str("http://example.net/foo/"),
            Url.from_str("http://example.net/foo/bar"),
        ),
        (
            "/bar",
            Url.from_str("http://example.net/foo"),
            Url.from_str("http://example.net/bar"),
        ),
        (
            "/bar",
            Url.from_str("http://example.net/foo/"),
            Url.from_str("http://example.net/bar"),
        ),
        (
            "http://example.org",
            Url.from_str("http://example.net"),
            Url.from_str("http://example.org"),
        ),
        (
            "//example.org",
            Url.from_str("http://example.net"),
            Url.from_str("http://example.org"),
        ),
        (
            "mailto:foo@example.net",
            Url.from_str("http://example.net"),
            None,
        ),
        (
            "tel:+0123",
            Url.from_str("http://example.net"),
            None,
        ),
    ],
)
def test_parse_href(href: str, base_url: Url, expected: Url):
    result = parse_href(href=href, base_url=base_url)

    assert result == expected
