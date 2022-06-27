import asyncio
from typing import AbstractSet

from .core import Url
from .link_extractor import get_links
from .monitor import Monitor
from .requester import Requester
from .url_store import UrlInfo, UrlStore


async def investigate_url(
    requester: Requester,
    url_store: UrlStore,
    start_url: Url,
    url: Url,
) -> AbstractSet[Url]:
    """
    Follow HTTP link and return new links if any are found.

    For external websites this only does a `HEAD` to know if the link is broken or not, so
    no new links are returned.
    """

    if url.netloc != start_url.netloc:
        result = await requester.get(url=url, use_head=True)

        if result.status_code() == 405:  # method not allowed
            result = await requester.get(url=url)

        return url_store.add_page(
            url=url,
            info=UrlInfo(result=result, links=None),
        )

    result = await requester.get(url=url)

    return url_store.add_page(
        url=url,
        info=UrlInfo(
            result=result,
            links=(get_links(url=url, result=result) if result.ok() else None),
        ),
    )


async def work(
    queue: asyncio.Queue[Url],
    requester: Requester,
    url_store: UrlStore,
    monitor: Monitor,
    start_url: Url,
):
    while True:
        task_url = await queue.get()
        monitor.on_task_start(queued=queue.qsize())
        try:
            new_urls = await investigate_url(
                requester=requester,
                url_store=url_store,
                start_url=start_url,
                url=task_url,
            )
            for url in new_urls:
                queue.put_nowait(url)
        finally:
            queue.task_done()

        monitor.on_task_done(
            queued=queue.qsize(),
            result=url_store.get_url_infos()[task_url].result,
        )
