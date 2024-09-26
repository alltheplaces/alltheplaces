from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.storefinders.elfsight import ElfsightSpider


class RabbaCASpider(ElfsightSpider):
    name = "rabba_ca"
    item_attributes = {"brand": "Rabba", "brand_wikidata": "Q109659398", "extras": Categories.SHOP_SUPERMARKET.value}
    host = "core.service.elfsight.com"
    shop = "https://rabba.com/locations/"
    api_key = "3df8be4a-1f05-46f7-86b4-f9dd7e4f717a"


    def post_process_item(self, item, response, location):
        item["name"] = location.get("infoTitle")
        if "24 HOURS" in location.get("infoWorkingHours").upper():
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            yield item
