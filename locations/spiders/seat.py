from typing import AsyncIterator

import xmltodict
from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.volkswagen import VolkswagenSpider


class SeatSpider(Spider):
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

    async def start(self) -> AsyncIterator[Request]:
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
                callback=VolkswagenSpider.parse_porsche_api,
                meta={"brand": self.item_attributes, "country": country, "crawler": self.crawler},
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
