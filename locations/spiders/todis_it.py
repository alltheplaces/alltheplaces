from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours


class TodisITSpider(Spider):
    name = "todis_it"
    item_attributes = {"brand": "Todis", "brand_wikidata": "Q3992174", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.todis.it"]
    start_urls = ["https://www.todis.it/wp-json/todis-stores/v1/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", callback=self.parse_store_list)

    def parse_store_list(self, response):
        for location in response.json():
            store_id = location["id"]
            yield JsonRequest(
                url=f"https://www.todis.it/wp-json/todis-stores/v1/store?id={store_id}", callback=self.parse_store
            )

    def parse_store(self, response):
        location = response.json()
        if location["store"]["active"] != "1":
            return

        item = DictParser.parse(location["store"])
        item["name"] = location["store"]["store"]
        item["street_address"] = item.pop("addr_full", None)
        item["city"] = location["comune"]["comune"]
        item["state"] = location["comune"]["regione"]
        item.pop("website", None)

        item["opening_hours"] = OpeningHours()
        for day_hours in location["orari"]:
            if day_hours["chiuso"] != "0":
                continue
            item["opening_hours"].add_range(DAYS_IT[day_hours["g"]], day_hours["a"], day_hours["c"])
            if day_hours["a_2"] and day_hours["c_2"]:
                item["opening_hours"].add_range(DAYS_IT[day_hours["g"]], day_hours["a_2"], day_hours["c_2"])

        yield item
