import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class DixyRUSpider(scrapy.Spider):
    name = "dixy_ru"
    item_attributes = {"brand": "Дикси", "brand_wikidata": "Q4161561"}
    allowed_domains = ["dixy.ru"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest("https://dixy.ru/local/ajax/components/dixy_shop_points.php")

    def parse(self, response):
        for store in response.json()["features"]:
            properties = store.get("properties", {})
            geometry = store.get("geometry", {})
            item = DictParser.parse(properties)
            item["addr_full"] = None
            item["street_address"] = properties.get("address")
            item["lat"] = geometry.get("coordinates")[0]
            item["lon"] = geometry.get("coordinates")[1]
            self.parse_hours(item, properties.get("workingHours"))
            yield item

    def parse_hours(self, item, hours):
        if hours == "24 часа":
            item["opening_hours"] = "24/7"
        else:
            item["opening_hours"] = f"Mo-Su {hours}"
        return item
