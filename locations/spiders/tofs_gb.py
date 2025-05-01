from scrapy import Spider

from locations.dict_parser import DictParser
from locations.categories import Categories, apply_category


class TofsGBSpider(Spider):
    name = "tofs_gb"
    item_attributes = {
        "brand": "The Original Factory Shop",
        "brand_wikidata": "Q7755366",
    }
    start_urls = ["https://api.storepoint.co/v1/15f4fbe5b10e3d/locations?rq"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)
            item["addr_full"] = item.pop("street_address")
            item["lat"] = location["loc_lat"]
            item["lon"] = location["loc_long"]
            item["branch"] = item["name"]
            item["name"] = "The Original Factory Shop"
            item.pop("website")
            item["facebook"] = location["facebook"]
            apply_categoy(Categories.SHOP_VARIETY_STORE, item)
            yield item
