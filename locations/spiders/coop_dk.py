from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class CoopDKSpider(scrapy.Spider):
    name = "coop_dk"
    BRANDS = {
        "Brugsen": {"brand_wikidata": "Q48772252"},
        "Coop365": {"brand_wikidata": "Q104671354"},
        "Dagli'Brugsen": {"brand_wikidata": "Q12307017"},
        "FK": {},
        "Irma": {"brand_wikidata": "Q797150"},
        "Kvickly": {"brand_wikidata": "Q7061148"},
        "SuperBrugsen": {"brand_wikidata": "Q12337746"},
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://info.coop.dk/umbraco/api/Chains/GetAllStores"
        headers = {"Accept": "application/json", "Origin": "https://info.coop.dk"}
        form = {
            "pageId": "19807",
            "hideClosedStores": "false",
        }
        yield scrapy.FormRequest(url, method="POST", formdata=form, headers=headers, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            location["street_address"] = location.pop("Address")
            location["ref"] = location.pop("Kardex")
            location["lon"] = location["Location"][0]
            location["lat"] = location["Location"][1]
            location["Zipcode"] = str(location["Zipcode"])
            location["website"] = "https://kampagner.coop.dk/find-butik/" + location.pop("UrlName")
            item = DictParser.parse(location)
            brand = location.pop("RetailGroupName")
            if brand == "Grønland":
                brand = "Brugsen"
            elif brand == "Coop.dk" or brand == "FaktaGermany":
                # Central warehouse for delivery, no actual supermarket
                continue
            item["brand"] = brand
            if item.get("lon") is not None and item["lon"] < -8.0:
                item["country"] = "GL"
            elif item.get("lon") is not None and item["lon"] <= -6.0:
                item["country"] = "FO"
            item.update(self.BRANDS.get(brand, {}))
            apply_category(Categories.SHOP_SUPERMARKET, item)
            if item["lon"] is not None and item["lat"] is not None:
                # Locations without coordinates are not real supermarkets, so can be removed
                yield item
