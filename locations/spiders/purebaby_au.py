import json
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PurebabyAUSpider(Spider):
    name = "purebaby_au"
    item_attributes = {"brand": "Purebaby", "brand_wikidata": "Q122431533"}
    allowed_domains = ["purebaby.com.au"]
    start_urls = ["https://purebaby.com.au/pages/stores"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        config = json.loads(response.xpath("//script[@data-stores-page-config]/text()").get())

        if response.url == self.start_urls[0]:
            param = config["paginationPageParam"]
            for page in range(2, config["paginationPages"] + 1):
                yield Request(url=f"{self.start_urls[0]}?{param}={page}")

        for location in config["stores"]:
            if location["type"] != "Store":
                continue
            item = DictParser.parse(location)
            item["branch"] = location["title"].removeprefix("Purebaby ")
            item["name"] = None
            item["image"] = location["image"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["openHours"])
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
