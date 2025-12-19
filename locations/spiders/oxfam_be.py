import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class OxfamBESpider(Spider):
    name = "oxfam_be"
    item_attributes = {"brand": "Oxfam", "brand_wikidata": "Q267941"}
    start_urls = ["https://oxfambelgie.be/shop-finder?type[winkel]=winkel&type[container]=container"]

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[contains(., "oxfam_store_locator")]/text()').get())
        for location in data["oxfam_store_locator"]["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["nid"]
            item["addr_full"] = location["adres"].replace("<br>", ",")

            if not location.get("store_url"):
                item["website"] = "https://oxfambelgie.be/shop-finder?type[container]=container"
                apply_category(Categories.RECYCLING, item)
                item["extras"]["recycling_type"] = "container"
            else:
                item["name"] = location["name"]
                item["website"] = location["store_url"]
                apply_category(Categories.SHOP_CHARITY, item)

            yield item
