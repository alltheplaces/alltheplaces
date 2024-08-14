from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MediriteZASpider(Spider):
    name = "medirite_za"
    item_attributes = {"brand_wikidata": "Q115696233"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}
    start_urls = ["https://www.medirite.co.za/bin/stores.json?national=yes&brand=medirite&country=198"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list, encoding="ISO-8859-1")

    def parse_store_list(self, response):
        for location in response.replace(body=response.text.encode().decode("unicode_escape")).json()["stores"]:
            if location["brand"] not in ["MediRite", "MediRite Plus"]:
                continue

            location["ref"] = location.pop("uid")

            location = {k: v for k, v in location.items() if v != "null"}

            location["phoneNumber"] = "+" + location["phoneInternationalCode"] + " " + location["phoneNumber"]

            if "physicalAdd3" in location and location["physicalAdd3"]:
                location["physicalAdd2"] += ", " + location["physicalAdd3"]
            if "physicalAdd2" in location and location["physicalAdd2"]:
                location["physicalAdd1"] += ", " + location["physicalAdd2"]
            location["street-address"] = location.pop("physicalAdd1")
            location["province"] = location.pop("physicalProvince")

            item = DictParser.parse(location)

            item["branch"] = location["branch"]
            item["brand"] = location["brand"]

            yield JsonRequest(
                url=f'https://www.medirite.co.za/bin/stores.json?uid={item["ref"]}',
                meta={"item": item},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        item = response.meta["item"]
        response = response.replace(body=response.text.encode().decode("unicode_escape"))
        # Same info as main stores.json response
        # location = response.json()["singleStoreData"][0]
        item["opening_hours"] = OpeningHours()
        for day_hours in response.json()["times"]:
            if day_hours["IsClosed"]:
                continue
            item["opening_hours"].add_range(day_hours["TradingDay"], day_hours["StartTime"], day_hours["EndTime"])
        yield item
