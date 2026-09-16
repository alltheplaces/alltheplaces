import json
import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class MapionSpider(Spider):
    """
    Storefinder platform used by several Japanese chains' store locator
    pages, hosted on mapion.co.jp subdomains/paths or on the brand's domain. If the paginated list of stores ends with `attr/?t=attr_con&start=1` then it's a Mapion spider. Listing pages are paginated with a "start" query
    parameter and stop once a page has no more detail links; detail pages
    embed the location's own data as a `window.infoJSON = {...};` blob.

    To use, set `feature_url_template` to a str.format() template for a listing page
    taking the page number, and optionally implement `post_process_item`.
    """

    feature_url_template: str

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.feature_url_template.format(1), meta={"page": 1}, callback=self.parse_list)

    def parse_list(self, response: Response) -> Iterable[Request]:
        hrefs = set(response.xpath('//a[contains(@href, "/info/")]/@href').getall())
        if not hrefs:
            return

        for href in hrefs:
            yield response.follow(href, callback=self.parse_detail)

        page = response.meta["page"] + 1
        yield Request(self.feature_url_template.format(page), meta={"page": page}, callback=self.parse_list)

    def parse_detail(self, response: Response) -> Iterable[Feature]:
        if not (m := re.search(r"window\.infoJSON\s*=\s*(\{.*?\});", response.text)):
            return
        data = json.loads(m.group(1))
        self.pre_process_data(data)

        item = DictParser.parse(data)
        item["extras"]["addr:province"] = data.get("kenname")
        if ruby := data.get("poi_name_yomi"):
            item["extras"]["branch:ja-Hira"] = ruby
        item["website"] = response.url
        yield from self.post_process_item(item, data, response) or []

    def pre_process_data(self, data: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
