import pytest

from discolinks.core import Link, LinkOrigin
from discolinks.html import get_hrefs, parse_href


@pytest.mark.parametrize(
    "body,expected",
    [
        ("<body></body>", []),
        ("""<a href="foo">""", ["foo"]),
        ("""<a href="foo#bar">""", ["foo#bar"]),
        ("""<a href="mailto:foo@example.net">""", []),
    ],
)
def test_get_hrefs(body: str, expected: list[tuple[Link, LinkOrigin]]):
    result = get_hrefs(body=body)

    assert list(result) == expected


@pytest.mark.parametrize(
    "href,base_link,expected",
    [
        (
            "",
            Link.from_url("http://example.net"),
            Link.from_url("http://example.net"),
        ),
        (
            "foo",
            Link.from_url("http://example.net"),
            Link.from_url("http://example.net/foo"),
        ),
        (
            "bar",
            Link.from_url("http://example.net/foo"),
            Link.from_url("http://example.net/bar"),
        ),
        (
            "bar",
            Link.from_url("http://example.net/foo/"),
            Link.from_url("http://example.net/foo/bar"),
        ),
        (
            "/bar",
            Link.from_url("http://example.net/foo"),
            Link.from_url("http://example.net/bar"),
        ),
        (
            "/bar",
            Link.from_url("http://example.net/foo/"),
            Link.from_url("http://example.net/bar"),
        ),
        (
            "http://example.org",
            Link.from_url("http://example.net"),
            Link.from_url("http://example.org"),
        ),
    ],
)
def test_parse_href(href: str, base_link: Link, expected: Link):
    result = parse_href(href=href, base_link=base_link)

    assert result == expected
