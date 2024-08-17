from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MediriteZASpider(Spider):
    name = "medirite_za"
    item_attributes = {"brand_wikidata": "Q115696233"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}
    start_urls = ["https://www.medirite.co.za/bin/stores.json?national=yes&brand=medirite&country=198"]
    base_url = "https://www.medirite.co.za"
    brands = ["MediRite", "MediRite Plus"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list, encoding="ISO-8859-1")

    def parse_store_list(self, response):
        for location in response.replace(body=response.text.encode().decode("unicode_escape")).json()["stores"]:
            if location["brand"] not in self.brands:
                continue

            location["ref"] = location.pop("uid")

            location = {k: v for k, v in location.items() if v != "null"}

            if "phoneInternationalCode" in location:
                location["phoneNumber"] = "+" + location["phoneInternationalCode"] + " " + location["phoneNumber"]

            location["street-address"] = ""
            for i in ["1", "2", "3"]:
                if ("physicalAdd" + i) in location:
                    location["street-address"] += location.pop("physicalAdd" + i) + ", "
            location["street-address"] = location["street-address"].rstrip(", ")

            if "physicalProvince" in location:
                location["province"] = location.pop("physicalProvince")

            item = DictParser.parse(location)

            item["branch"] = location["branch"]
            item["brand"] = location["brand"]

            yield JsonRequest(
                url=f'{self.base_url}/bin/stores.json?uid={item["ref"]}',
                meta={"item": item},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        item = response.meta["item"]
        response = response.replace(body=response.text.encode().decode("unicode_escape"))
        # Same info as main stores.json response
        # location = response.json()["singleStoreData"][0]

        services = [s["FacilityTypeName"] for s in response.json()["services"]]
        # Many other services can be listed for Checkers and LiquorShop, but not all refer to in-store facilities. Some are just available nearby
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Friendly" in services)

        item["opening_hours"] = OpeningHours()
        for day_hours in response.json()["times"]:
            if day_hours["IsClosed"]:
                continue
            item["opening_hours"].add_range(day_hours["TradingDay"], day_hours["StartTime"], day_hours["EndTime"])
        yield item
