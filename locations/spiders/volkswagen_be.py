from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.audi import AudiSpider
from locations.spiders.seat import SeatSpider


class VolkswagenBESpider(Spider):
    name = "volkswagen_be"
    BRANDS = {
        "AU": AudiSpider.item_attributes,
        "SE": SeatSpider.item_attributes,
        "VW": {"brand": "Volkswagen", "brand_wikidata": "Q246"},
        "CV": {"brand": "Volkswagen Commercial Vehicles", "brand_wikidata": "Q699709"},
        "CU": {"brand": "Cupra", "brand_wikidata": "Q8352675"},
        "MW": {"brand": "My Way", "brand_wikidata": ""},
    }
    #   templateId: 48-SEAT, 49-Audi, 50-Volkswagen, 51-Volkswagen Commercial, 58-My Way, 98-Cupra
    start_urls = [
        f"https://dealerlocator-api.dieteren.be/api/workLocations?templateId={id}" for id in [48, 49, 50, 51, 58, 98]
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Dealers"]:
            item = DictParser.parse(location)
            item["ref"] = location.get("WorkLocationId")
            brand = location.get("BRAND")
            item["ref"] = item["ref"] + brand  # update ref to avoid dropping same location for different brands
            if brand_info := self.BRANDS.get(brand):
                item.update(brand_info)
            item["lat"] = location.get("GPSLAT")
            item["lon"] = location.get("GPSLONG")
            item["street_address"] = item.pop("addr_full")
            item["email"] = location.get("MAIL")
            item["website"] = "https://dealerlocator.volkswagen.be/fr"
            item["extras"]["website_2"] = location.get("URL")
            if location.get("VENTE"):  # Sale
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no("second_hand", item, item["brand"] == "My Way")
            else:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            apply_yes_no("service:vehicle:car_repair", item, location.get("APRESVENTE"))  # After Sale
            yield item
