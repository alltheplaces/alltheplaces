from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PetValuCASpider(Spider):
    name = "pet_valu_ca"
    PET_VALUE = {"brand": "Pet Valu", "brand_wikidata": "Q58009635"}
    allowed_domains = ["store.petvalu.ca"]
    start_urls = [
        "https://store.petvalu.ca/stat/api/locations/search?lng=-73.9818&lat=40.7263&kilometers=3000&limit=20000&fields=servicetags_bosleys,servicetags_paulmacs,servicetags_tisol_2,servicetags_total_pet_2,servicetags_petvalu_2,displayname_location_name",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["locations"]:
            store.update(store.pop("businessAddress"))
            item = DictParser.parse(store)
            item["ref"] = store["clientLocationId"]
            item["lon"], item["lat"] = store["coordinates"]
            item["phone"] = store["primaryPhone"]
            item["website"] = urljoin("https://store.petvalu.ca/store/", store["link"])
            item["branch"] = store["displayFields"]["displayname_location_name"]

            item["opening_hours"] = OpeningHours()
            for day, rule in store["hours"].items():
                for times in rule["blocks"]:
                    item["opening_hours"].add_range(day, times["from"], times["to"], "%H%M")

            if store["businessName"] == "Pet Valu":
                item.update(self.PET_VALUE)
            else:
                item["brand"] = item["name"] = store["businessName"]

            apply_category(Categories.SHOP_PET, item)

            yield item
