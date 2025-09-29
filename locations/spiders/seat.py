from copy import deepcopy
from typing import Any

import reverse_geocoder
import scrapy
import xmltodict
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class SeatSpider(scrapy.Spider):
    name = "seat"
    item_attributes = {"brand": "Seat", "brand_wikidata": "Q188217"}
    COUNTRY_DEALER_LOCATOR_MAP = {
        "fr": "trouver-un-distributeur",
        "it": "concessionari",
        "uk": "car-dealers-locator",
        "es": "red-de-concesionarios-seat",
        "ie": "car-dealers-locator",
        "gr": "car-dealer-locator",
        "mx": "concesionarias",
        "ch": "de/haendlersuche",
        "se": "hitta-aterforsaljare",
        "pl": "mapa-dealerow-i-serwisow",
        "lu": "car-dealer-locator",
        "fi": "yhteystiedot/jalleenmyyjahaku",
        "nl": "car-dealer-locator",
    }

    available_countries_porsche_api = [
        "AL",
        "AT",
        "BA",
        "CL",
        "CO",
        "CZ",
        "HR",
        "HU",
        "MK",
        "PT",
        "RO",
        "RS",
        "SG",
        "SI",
        "SK",
        "UA",
    ]

    def start_requests(self):
        for country, locator in self.COUNTRY_DEALER_LOCATOR_MAP.items():
            yield Request(
                url=f"https://www.seat.{country}/{locator}.snw.xml?brandseat=true&max_dist=3000&city={country.upper()}".replace(
                    "seat.it", "seat-italia.it"
                ).replace(
                    "seat.uk", "seat.co.uk"
                )
            )

        for country in self.available_countries_porsche_api:
            yield Request(
                url=f"https://groupcms-services-api.porsche-holding.com/v3/dealers/{country}/S",
                callback=self.parse_porsche_api,
            )

    def parse(self, response):
        data = xmltodict.parse(response.text)
        for store in data.get("result-list", {}).get("partner"):
            store.update(store.pop("mapcoordinate", {}))
            item = DictParser.parse(store)
            item = self.repair_website(item)
            item["ref"] = store.get("partner_id")
            item["street_address"] = item.pop("street", "")
            item["phone"] = store.get("phone1")
            item["extras"]["fax"] = store.get("fax1")
            if store["types"]["type"] == "D":
                apply_category(Categories.SHOP_CAR, item)
            elif store["types"]["type"] == "S":
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item

    def parse_porsche_api(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("data"):
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["ref"] = store["bnr"]
            item["state"] = store.get("federalState")
            offers = store.get("contracts", {})
            # Locations in ME have country property equal to RS
            if item.get("lat") and item.get("lon"):
                if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
                    if item["country"] != result["cc"] and item["country"] == "RS":
                        item["country"] = result["cc"]
            if offers.get("sales"):
                yield self.build_categorized_item(item, Categories.SHOP_CAR)
            if offers.get("service"):
                yield self.build_categorized_item(item, Categories.SHOP_CAR_REPAIR)

    def build_categorized_item(self, item: Feature, category: Categories) -> Feature:
        c_item = deepcopy(item)
        c_item["ref"] = f"{item['ref']}-{category}"
        apply_category(category, c_item)
        return c_item

    def repair_website(self, item):
        if website := item["website"]:
            if website.startswith("https://"):
                item["website"] = website
            elif website.startswith("http://"):
                item["website"] = website.replace("http://", "https://")
            elif website.startswith("www."):
                item["website"] = website.replace("www.", "https://www.")
            elif "@" in website:
                item["email"] = item.pop("website")
            elif item["website"] == "-":
                item["website"] = None
            else:
                item["website"] = "https://" + website
        return item
