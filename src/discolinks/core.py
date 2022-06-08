from typing import Optional
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
        assert parsed.scheme
        assert parsed.netloc
        return cls(
            full=urldefrag(url).url,
            scheme=parsed.scheme,
            netloc=parsed.netloc,
        )

    def __str__(self) -> str:
        return self.full


@attrs.frozen
class LinkOrigin:
    """
    Information about the origin of a link.

    - `link.url` is the address where the link was found.
     -`link.href` is the HTML "href" attribute of the link.
    """

    url: Url
    href: str


@attrs.frozen
class LinkInfo:
    status_code: Optional[int]
    origins: frozenset[LinkOrigin]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)

    def add_origin(self, origin: LinkOrigin) -> "LinkInfo":
        return LinkInfo(
            status_code=self.status_code, origins=self.origins | frozenset([origin])
        )
