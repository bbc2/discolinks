from typing import Optional
from urllib.parse import urldefrag, urlparse

import attrs


@attrs.frozen
class Link:
    url: str
    scheme: str
    netloc: str

    @classmethod
    def from_url(cls, url: str) -> "Link":
        parsed = urlparse(url)
        assert parsed.scheme
        assert parsed.netloc
        return cls(
            url=urldefrag(url).url,
            scheme=parsed.scheme,
            netloc=parsed.netloc,
        )


@attrs.frozen
class LinkOrigin:
    page: Link
    href: str


@attrs.frozen
class LinkInfo:
    status_code: Optional[int]
    origins: frozenset[LinkOrigin]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)
