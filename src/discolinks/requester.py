import logging

import attrs
import requests
from requests_html import AsyncHTMLSession, HTMLResponse

from .core import Link

logger = logging.getLogger(__name__)


@attrs.frozen
class RequestError(Exception):
    msg: str


@attrs.frozen
class Requester:
    session: AsyncHTMLSession = attrs.field(init=False, factory=AsyncHTMLSession)

    async def get(self, link: Link) -> HTMLResponse:
        """
        Fetch an HTML page from the given link.

        Raises `RequestError` if any connection issue is encountered.
        """
        logger.debug("Requesting %s", link.url)

        try:
            response = await self.session.get(link.url)
        except requests.RequestException as error:
            raise RequestError(msg=str(error))

        return response
