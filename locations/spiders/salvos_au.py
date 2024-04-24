import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SalvosAUSpider(Spider):
    name = "salvos_au"
    item_attributes = {"brand": "Salvos", "brand_wikidata": "Q120646407"}
    allowed_domains = ["www.salvosstores.com.au"]
    start_urls = ["https://www.salvosstores.com.au/api/uplister/store-list"]

    def parse(self, response):
        for location in response.json().values():
            if location.get("isPermanentlyClosed") or location.get("isOpeningSoon"):
                continue
            item = DictParser.parse(location)
            item["addr_full"] = re.sub(r"\s+", " ", location["FullAddress"].replace("<br>", ", ")).strip()
            item["housenumber"] = location["Number"]
            item["street"] = " ".join(filter(None, [location["StreetName"], location["StreetType"]]))
            item["city"] = location["SuburbName"]
            item["website"] = location["URL"].replace("uplister.com.au", "www.salvosstores.com.au/stores")
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location["OpeningHours"].items():
                if day_hours == "Close":
                    continue
                item["opening_hours"].add_range(day_name, day_hours["Opening"], day_hours["Closing"], "%H:%M:%S")
            apply_category(Categories.SHOP_CHARITY, item)
            yield item
