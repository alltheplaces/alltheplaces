import json
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HoulihansUSSpider(Spider):
    name = "houlihans_us"
    item_attributes = {"brand": "Houlihan's", "brand_wikidata": "Q5913100s"}
    allowed_domains = ["houlihans.com"]
    start_urls = ["https://www.houlihans.com/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in json.loads(response.xpath('//*[@type="application/ld+json"]/text()').get())["subOrganization"]:
            item = DictParser.parse(store)
            item["ref"] = item["website"]
            apply_category(Categories.RESTAURANT, item)
            yield Request(url=item["website"], callback=self.parse_location, meta={"item": item})

    def parse_location(self, response, **kwargs):
        item = response.meta["item"]
        item["lat"] = response.xpath("//@data-gmaps-lat").get()
        item["lon"] = response.xpath("//@data-gmaps-lng").get()
        yield item
