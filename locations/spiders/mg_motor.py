import html
import json
import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# One map page per country. Belgium and Switzerland have one page per
# language with the same stores, so only one language is listed.
EUROPE_MAP_PAGES = {
    "AL": "https://www.mgmotor.al/map",
    "AT": "https://www.mgmotor.eu/de-AT/map",
    "BA": "https://www.mgmotor.ba/map",
    "BE": "https://www.mgmotor.be/fr/map",
    "BG": "https://www.mgmotor.bg/map",
    "CH": "https://www.mgmotor.ch/de/map",
    "CY": "https://www.mgmotor.cy/map",
    "DE": "https://www.mgmotor.de/map",
    "EE": "https://www.mgmotor.ee/map",
    "ES": "https://www.mgmotor.es/map",
    "FI": "https://www.mgmotor.fi/map",
    "FR": "https://www.mgmotor.fr/map",
    "HR": "https://www.mgmotor.hr/map",
    "HU": "https://www.mgmotor.hu/map",
    "IE": "https://www.mg.ie/map",
    "IS": "https://www.mgmotor.is/map",
    "IT": "https://www.mgmotor.it/map",
    "LT": "https://www.mgmotor.lt/map",
    "LU": "https://www.mgmotor.lu/map",
    "LV": "https://www.mgmotor.lv/map",
    "MK": "https://www.mgmotor.mk/map",
    "MT": "https://www.mgmotor.mt/map",
    "NL": "https://www.mgmotor.nl/map",
    "NO": "https://www.mgmotors.no/map",
    "PL": "https://www.mgmotor.pl/map",
    "PT": "https://www.mgmotor.pt/map",
    "RS": "https://www.mgmotor.rs/map",
    "SE": "https://www.mgmotor.eu/sv-SE/map",
    "SI": "https://www.mgmotor.si/map",
}


class MgMotorSpider(Spider):
    name = "mg_motor"
    item_attributes = {"brand": "MG", "brand_wikidata": "Q1881443"}

    async def start(self) -> AsyncIterator[Request]:
        for country, url in EUROPE_MAP_PAGES.items():
            yield Request(url=url, callback=self.parse_europe, cb_kwargs={"country": country})
        yield JsonRequest(url="https://www.mg.co.uk/api/all-dealers", callback=self.parse_gb)

    def parse_europe(self, response: Response, country: str) -> Any:
        stores = re.search(r'<brand-stores-map-component[^>]*?\s:stores="([^"]*)"', response.text)
        if not stores:
            return
        for store in json.loads(html.unescape(stores.group(1))):
            item = Feature()
            item["ref"] = store["id"]
            item["name"] = store["title"]
            item["lat"] = self.clean_coordinate(store["lat"])
            item["lon"] = self.clean_coordinate(store["lng"])
            item["street_address"] = store["street"]
            item["postcode"] = store["zip"]
            item["city"] = store["city"]
            item["country"] = country
            item["phone"] = store["phone"]
            item["email"] = store["email"]
            # Each site lists sales and servicing as separate entries.
            store_type = (store.get("specialStoreType") or {}).get("value")
            if store_type == "serviceStore":
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                apply_category(Categories.SHOP_CAR, item)
            yield item

    @staticmethod
    def clean_coordinate(value: str | None) -> float | None:
        # A few entries have a trailing comma or are written like "8.2758° W".
        if m := re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*°?\s*([NSEW])?\s*,?\s*", value or ""):
            coordinate = float(m.group(1))
            if m.group(2) in ("S", "W"):
                coordinate = -abs(coordinate)
            return coordinate
        return None

    def parse_gb(self, response: Response) -> Any:
        for dealer in response.json():
            item = Feature()
            item["ref"] = dealer["mg_id"]
            item["name"] = dealer["name"]
            if m := re.match(r"^(-?\d+\.\d+)\s+(-?\d+\.\d+)$", dealer.get("latitude_longitude") or ""):
                item["lat"], item["lon"] = m.groups()
            # address2 holds the town and town holds the county.
            item["street_address"] = dealer.get("address1")
            item["city"] = dealer.get("address2")
            item["postcode"] = dealer.get("postcode")
            item["country"] = "GB"
            item["website"] = dealer.get("website")

            if dealer.get("dealer_type_sales") == "True":
                sales_item = item.deepcopy()
                sales_item["ref"] = "{}_Sales".format(item["ref"])
                sales_item["phone"] = dealer.get("phoneNumber")
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item
            if dealer.get("dealer_type_service") == "True":
                service_item = item.deepcopy()
                service_item["ref"] = "{}_Service".format(item["ref"])
                service_item["phone"] = dealer.get("after_sales_phoneNumber") or dealer.get("phoneNumber")
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
