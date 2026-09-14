from typing import AsyncIterator, Iterable, Iterator
from urllib.parse import urlsplit

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature


class AreamarkerSpider(Spider):
    """
    Store locator platform by AreaMarker (areamarker.com). POIs are served by
    an OpenSearch-backed JSON API (ss-api.areamarker.com or a brand subdomain)
    whose "search-by-condition" endpoint pages through results with a `search_after`
    cursor.

    The API rejects requests without the `Origin`/`Referer` headers and the
    per-brand `X-Amss-Shopsite-Corp-ID` header, so those must be supplied.
    `Origin` is derived from `referer` (its scheme + netloc).

    To use, set `api_url`, `corp_id`, `referer`, and `fields` (the list of API
    columns to request). `search_conditions` and `page_size` may be overridden
    per brand. Then implement `post_process_item` to build a Feature from each
    raw API record.
    """

    dataset_attributes = {"source": "api", "api": "areamarker.com"}

    api_url: str
    corp_id: str
    referer: str
    fields: list[str]
    search_conditions: list[dict] = []
    page_size: int = 500

    def make_request(self, search_after: list | None = None) -> JsonRequest:
        body = {
            "search_conditions": self.search_conditions,
            "fields": self.fields,
            "paging_mode": "search_after",
            "sort": "+pre_code,+city_code,+kyo_id",
            "corp_id": self.corp_id,
            "size": self.page_size,
        }
        if search_after:
            body["search_after"] = search_after
        split = urlsplit(self.referer)
        headers = {
            "X-Amss-Shopsite-Corp-ID": self.corp_id,
            "Origin": f"{split.scheme}://{split.netloc}",
            "Referer": self.referer,
        }
        return JsonRequest(self.api_url, data=body, headers=headers)

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request()

    def parse(self, response: TextResponse) -> Iterator[Feature | JsonRequest]:
        hits = response.json()["result"]["hits"]
        for record in hits.get("hit", []):
            yield from self.post_process_item(record, response) or []

        # `search_after` cursor pagination requires following the cursor
        # returned by the previous page, so the next request is issued from here.
        search_after = hits.get("search_after")
        if search_after:
            yield self.make_request(search_after)

    def post_process_item(self, record: dict, response: TextResponse) -> Iterable[Feature]:
        """Override to build one or more Features from a raw API record."""
        return []
