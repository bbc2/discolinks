import logging

import attrs
import httpx

from .core import Url

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
    client: httpx.AsyncClient = attrs.field(init=False, factory=httpx.AsyncClient)

    async def head(self, link: Url) -> HeadResponse:
        """
        Send a HEAD request to the given link.

        Raises `RequestError` if any connection issue is encountered.
        """
        logger.debug("HEAD %s", link)

        try:
            response = await self.client.head(link.full, follow_redirects=True)
        except httpx.HTTPError as error:
            raise RequestError(msg=str(error))

        return HeadResponse(
            status_code=response.status_code,
        )

    async def get(self, link: Url) -> GetResponse:
        """
        Fetch an HTML page from the given link.

        Raises `RequestError` if any connection issue is encountered.
        """
        logger.debug("GET %s", link)

        try:
            response = await self.client.get(link.full, follow_redirects=True)
        except httpx.HTTPError as error:
            raise RequestError(msg=str(error))

        return GetResponse(
            status_code=response.status_code,
            body=response.text,
        )
