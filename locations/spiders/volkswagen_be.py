from copy import deepcopy
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class VolkswagenBESpider(Spider):
    name = "volkswagen_be"
    BRANDS = {
        "SE": {"brand": "Seat", "brand_wikidata": "Q188217"},
        "VW": {"brand": "Volkswagen", "brand_wikidata": "Q246"},
        "CV": {"brand": "Volkswagen Commercial Vehicles", "brand_wikidata": "Q699709"},
        "MW": {"brand": "My Way", "brand_wikidata": ""},
        "CU": {"brand": "Cupra", "brand_wikidata": "Q8352675"},
    }
    # templateId: 12-SEAT, 50-Volkswagen, 51-Volkswagen Commercial, 58-My Way, 98-Cupra
    start_urls = [
        f"https://dealerlocator-api.dieteren.be/api/workLocations?templateId={id}" for id in [12, 50, 51, 58, 98]
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Dealers"]:
            item = DictParser.parse(location)
            item["ref"] = location.get("WorkLocationId")
            brand = location.get("BRAND")
            item["ref"] = item["ref"] + brand  # update ref to avoid dropping same location for different brands
            if brand_info := self.BRANDS.get(brand):
                item["brand"] = brand_info["brand"]
                item["brand_wikidata"] = brand_info["brand_wikidata"]
            item["lat"] = location.get("GPSLAT")
            item["lon"] = location.get("GPSLONG")
            item["street_address"] = item.pop("addr_full")
            item["email"] = location.get("MAIL")
            if item.get("website") and not item["website"].startswith("http"):
                item["website"] = "https://" + item["website"]
            if location.get("VENTE"):  # Sale
                shop_item = deepcopy(item)
                shop_item["ref"] = f"{item['ref']}-SHOP"
                apply_category(Categories.SHOP_CAR, shop_item)
                apply_yes_no(Extras.USED_CAR_SALES, item, item["brand"] == "My Way")
                yield shop_item
            if location.get("APRESVENTE"):  # After Sale
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-SERVICE"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
