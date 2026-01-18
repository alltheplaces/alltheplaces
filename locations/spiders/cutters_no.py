from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CuttersNOSpider(Spider):
    name = "cutters_no"
    allowed_domains = ["cutters.no"]
    item_attributes = {"brand": "Cutters", "brand_wikidata": "Q106940660"}
    start_urls = ["https://cutters.no/api/salons/country/NO"]

    def parse(self, response):
        for salon in response.json().get("salons"):
            if not salon.get("active"):
                continue

            item = DictParser.parse(salon)

            item["branch"] = item.pop("name")
            item["city"] = salon.get("postalPlace")
            item["street_address"] = salon.get("address")
            item.pop("addr_full")

            if relativeLocation := salon.get("relativeLocation"):
                item["extras"]["description"] = relativeLocation

            if coordinates := salon.get("coordinates"):
                item["lat"] = coordinates.get("latitude")
                item["lon"] = coordinates.get("longitude")

            apply_category(Categories.SHOP_HAIRDRESSER, item)
            yield item
