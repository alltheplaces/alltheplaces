import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsHRSpider(scrapy.Spider):
    name = "mcdonalds_hr"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.hr/api/locations/"]

    def parse(self, response, **kwargs):
        for location in response.json()["payload"]["locations"]:
            location.update(location.pop("data"))
            item = DictParser.parse(location)
            item.pop("addr_full")
            item["street_address"] = location["address"]

            apply_yes_no(Extras.DRIVE_THROUGH, item, location["has_drive"], True)
            apply_yes_no(Extras.DELIVERY, item, location["has_delivery"], True)

            apply_category(Categories.FAST_FOOD, item)

            yield item
