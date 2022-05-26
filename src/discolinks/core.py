from typing import Optional

import attrs


@attrs.frozen
class Link:
    url: str
    scheme: str
    netloc: str


@attrs.frozen
class LinkInfo:
    status_code: Optional[int]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)
