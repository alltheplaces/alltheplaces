import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MarksAndSpencerSpider(CrawlSpider):
    name = "marks_and_spencer"
    item_attributes = {"brand": "Marks & Spencer", "brand_wikidata": "Q714491"}
    start_urls = ["https://www.marksandspencer.com/store-listing"]
    rules = [Rule(LinkExtractor(allow=r"/stores/[^/]+$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        json_data = DictParser.get_nested_key(
            json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get()), "store"
        )
        item = DictParser.parse(json_data)
        item["housenumber"] = item.pop("street_address")
        item["street"] = json_data.get("address").get("addressLine2")
        if "-bp-" in response.url:
            item["located_in"] = "BP"
            item["located_in_wikidata"] = "Q152057"
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "-simply-food-" in response.url:
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "-foodhall-" in response.url:
            item["name"] = "M&S Foodhall"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "-moto-simply-food-" in response.url:
            item["operator"] = "Moto"
            item["operator_wikidata"] = "Q6917970"
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            item["name"] = "Marks & Spencer"
            apply_category(Categories.GENERIC_SHOP, item)

        yield item
