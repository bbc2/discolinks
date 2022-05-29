import logging

import attrs
import requests
from requests_html import AsyncHTMLSession

from .core import Link

logger = logging.getLogger(__name__)


@attrs.frozen
class RequestError(Exception):
    msg: str


def status_code_ok(status_code: int) -> bool:
    return not (400 <= status_code < 600)


@attrs.frozen
class HeadResponse:
    status_code: int

    def ok(self) -> bool:
        return status_code_ok(self.status_code)


@attrs.frozen
class GetResponse:
    status_code: int
    body: str

    def ok(self) -> bool:
        return status_code_ok(self.status_code)


@attrs.frozen
class Requester:
    session: AsyncHTMLSession = attrs.field(init=False, factory=AsyncHTMLSession)

    async def head(self, link: Link) -> HeadResponse:
        """
        Send a HEAD request to the given link.

        Raises `RequestError` if any connection issue is encountered.
        """
        logger.debug("HEAD %s", link.url)

        try:
            response = await self.session.head(link.url)
        except requests.RequestException as error:
            raise RequestError(msg=str(error))

        return HeadResponse(
            status_code=response.status_code,
        )

    async def get(self, link: Link) -> GetResponse:
        """
        Fetch an HTML page from the given link.

        Raises `RequestError` if any connection issue is encountered.
        """
        logger.debug("GET %s", link.url)

        try:
            response = await self.session.get(link.url)
        except requests.RequestException as error:
            raise RequestError(msg=str(error))

        return GetResponse(
            status_code=response.status_code,
            body=response.text,
        )
