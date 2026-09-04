import json
import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature


class MapionSpider(Spider):
    """
    Storefinder platform used by several Japanese chains' store locator
    pages, hosted on mapion.co.jp subdomains/paths (e.g. Mister Donut,
    NTT Le Perc). Listing pages are paginated with a "start" query
    parameter and stop once a page has no more detail links; detail pages
    embed the location's own data as a `window.infoJSON = {...};` blob.

    To use, set `list_url` to a str.format() template for a listing page
    taking the page number, and implement `parse_item`.
    """

    list_url = ""

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.list_url.format(1), meta={"page": 1}, callback=self.parse_list)

    def parse_list(self, response: Response) -> Iterable[Request]:
        hrefs = set(response.xpath('//a[contains(@href, "/info/")]/@href').getall())
        if not hrefs:
            return

        for href in hrefs:
            yield response.follow(href, callback=self.parse_detail)

        page = response.meta["page"] + 1
        yield Request(self.list_url.format(page), meta={"page": page}, callback=self.parse_list)

    def parse_detail(self, response: Response) -> Iterable[Feature]:
        if not (m := re.search(r"window\.infoJSON\s*=\s*(\{.*?\});", response.text)):
            return
        data = json.loads(m.group(1))

        item = Feature()
        item["website"] = response.url
        yield from self.parse_item(item, data, response) or []

    def parse_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        raise NotImplementedError
