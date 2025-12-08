from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, DELIMITERS_ES, OpeningHours


class MetroPESpider(Spider):
    name = "metro_pe"
    item_attributes = {"brand": "Metro", "brand_wikidata": "Q16640217", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.metro.pe"]
    start_urls = ["https://www.metro.pe/files/store.json"]

    def parse(self, response):
        locations = []
        for region in response.json().values():
            for office in region["offices"]:
                office["id"] = region["name"] + str(office["id"])
                locations.append(office)

        for location in locations:
            if not location["active"]:
                continue
            item = DictParser.parse(location)
            item.pop("phone", None)
            item["opening_hours"] = OpeningHours()
            for schedule in location["schedule"]:
                item["opening_hours"].add_ranges_from_string(schedule, days=DAYS_ES, delimiters=DELIMITERS_ES)
            yield item
