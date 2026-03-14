from urllib.parse import urljoin

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CrossFitSpider(scrapy.Spider):
    name = "cross_fit"
    item_attributes = {"brand": "CrossFit", "brand_wikidata": "Q2072840"}
    start_urls = ["https://www.crossfit.com/wp-content/uploads/affiliates.json"]

    def parse(self, response):
        for location in response.json()["features"]:
            item = DictParser.parse(location["properties"])
            item["street_address"] = item.pop("street", "")
            item.pop("addr_full", None)
            item["geometry"] = location["geometry"]
            item["ref"] = item["website"] = urljoin("https://www.crossfit.com/", location["properties"]["slug"])
            item["image"] = location["properties"]["images"]["primary"]["url"]

            apply_category(Categories.GYM, item)
            yield item
