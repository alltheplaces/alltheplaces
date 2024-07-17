import scrapy
import xmltodict
from scrapy import Request

from locations.dict_parser import DictParser


class SeatSpider(scrapy.Spider):
    name = "seat"
    item_attributes = {
        "brand": "SEAT",
        "brand_wikidata": "Q188217",
    }
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
    }

    def start_requests(self):
        for country, locator in self.COUNTRY_DEALER_LOCATOR_MAP.items():
            yield Request(
                url=f"https://www.seat.{country}/{locator}.snw.xml?brandseat=true&max_dist=3000&city={country.upper()}".replace(
                    "seat.it", "seat-italia.it"
                ).replace(
                    "seat.uk", "seat.co.uk"
                )
            )

    def parse(self, response):
        data = xmltodict.parse(response.text)
        for store in data.get("result-list", {}).get("partner"):
            store.update(store.pop("mapcoordinate", {}))
            item = DictParser.parse(store)
            item["ref"] = store.get("partner_id")
            item["street_address"] = item.pop("street", "")
            item["phone"] = store.get("phone1")
            item["extras"]["fax"] = store.get("fax1")
            yield item
