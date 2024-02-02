from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PetrolSpider(Spider):
    name = "petrol"
    CRODUX = {"brand": "Crodux", "brand_wikidata": "Q62274622"}
    PETROL = {"brand": "Petrol", "brand_wikidata": "Q174824"}
    item_attributes = PETROL

    @staticmethod
    def make_request(offset):
        return JsonRequest(
            f"https://www.petrol.eu/restservices/sales-service/filterStores?offset={offset}", meta={"offset": offset}
        )

    def start_requests(self):
        yield self.make_request(0)

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["status"] != "ACTIVE":
                continue
            location["location"] = location["location"]["coordinates"][0]

            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for day, times in location["activeOpeningHours"]["times"].items():
                for time_range in times:
                    item["opening_hours"].add_range(day, time_range["open"], time_range["close"])

            for cat in location["storeCharacteristics"]:
                if cat["characteristic"]["key"] == "28":
                    item.update(self.CRODUX)
                elif cat["characteristic"]["key"] == "160":
                    apply_yes_no(Fuel.DIESEL, item, True)
                elif cat["characteristic"]["key"] == "191":
                    apply_yes_no(Extras.WIFI, item, True)

            apply_category(Categories.FUEL_STATION, item)
            yield item

        if len(response.json()) == 100:
            yield self.make_request(response.meta["offset"] + 100)
