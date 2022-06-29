from urllib.parse import urldefrag, urlparse

import attrs


@attrs.frozen
class Url:
    """
    Wrapper around URL strings.

    Use `Url.from_str` to build an instance and `url.full` to get the underlying string
    (e.g. for communicating with HTTP libraries).
    """

    full: str
    scheme: str
    netloc: str

    @classmethod
    def from_str(cls, url: str) -> "Url":
        parsed = urlparse(url)
        assert parsed.scheme, f"Invalid URL: {url}"
        assert parsed.netloc, f"Invalid URL: {url}"
        return cls(
            full=urldefrag(url).url,
            scheme=parsed.scheme,
            netloc=parsed.netloc,
        )

    def __str__(self) -> str:
        return self.full


@attrs.frozen
class Link:
    href: str
    url: Url
