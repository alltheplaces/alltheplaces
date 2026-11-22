import html
import json
import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# One map page per country. Belgium and Switzerland have one page per
# language with the same stores, so only one language is listed.
EUROPE_MAP_PAGES = {
    "AL": "https://www.mgmotor.al/map",
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
    "IS": "https://www.mgmotor.is/map",
    "IT": "https://www.mgmotor.it/map",
    "LT": "https://www.mgmotor.lt/map",
    "LU": "https://www.mgmotor.lu/map",
    "LV": "https://www.mgmotor.lv/map",
    "MK": "https://www.mgmotor.mk/map",
    "MT": "https://www.mgmotor.mt/map",
    "PT": "https://www.mgmotor.pt/map",
    "RS": "https://www.mgmotor.rs/map",
    "SI": "https://www.mgmotor.si/map",
}

# These sites don't embed the store map component; they publish a JSON-LD ItemList instead.
JSONLD_MAP_PAGES = {
    "AT": "https://www.mgmotor.at/map",
    "HU": "https://www.mgmotor.hu/map",
    "IE": "https://www.mg.ie/map",
    "NL": "https://www.mgmotor.nl/map",
    "NO": "https://www.mgmotors.no/map",
    "PL": "https://www.mgmotor.pl/map",
    "SE": "https://www.mg.se/map",
}


class MgMotorSpider(Spider):
    name = "mg_motor"
    item_attributes = {"brand": "MG", "brand_wikidata": "Q1881443"}

    async def start(self) -> AsyncIterator[Request]:
        for country, url in EUROPE_MAP_PAGES.items():
            yield Request(url=url, callback=self.parse_europe, cb_kwargs={"country": country})
        for country, url in JSONLD_MAP_PAGES.items():
            yield Request(url=url, callback=self.parse_jsonld, cb_kwargs={"country": country})

    def parse_europe(self, response: Response, country: str) -> Any:
        stores = re.search(r'<brand-stores-map-component[^>]*?\s:stores="([^"]*)"', response.text)
        for store in json.loads(html.unescape(stores.group(1))):
            item = Feature()
            item["ref"] = store["id"]
            item["name"] = store["title"]
            # A few entries have a trailing comma or are written like "8.2758° W".
            for field, key in (("lat", "lat"), ("lon", "lng")):
                if m := re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*°?\s*([NSEW])?\s*,?\s*", store[key]):
                    item[field] = -abs(float(m.group(1))) if m.group(2) in ("S", "W") else float(m.group(1))
            item["street_address"] = store["street"]
            item["postcode"] = store["zip"]
            item["city"] = store["city"]
            item["country"] = country
            item["phone"] = store["phone"]
            item["email"] = store["email"]
            # Each site lists sales and servicing as separate entries.
            if store["specialStoreType"]["value"] == "serviceStore":
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                apply_category(Categories.SHOP_CAR, item)
            yield item

    def parse_jsonld(self, response: Response, country: str) -> Iterable[Feature]:
        dealers = json.loads(
            response.xpath('//script[@type="application/ld+json"][contains(., "ItemList")]/text()').get()
        )
        for entry in dealers["itemListElement"]:
            dealer = entry["item"]
            item = Feature()
            item["ref"] = "{}_{}".format(dealer["name"], dealer["address"]["streetAddress"])
            item["name"] = dealer["name"]
            item["street_address"] = dealer["address"]["streetAddress"]
            item["postcode"] = dealer["address"]["postalCode"]
            item["city"] = dealer["address"]["addressLocality"]
            item["country"] = country
            item["lat"] = dealer["geo"]["latitude"]
            item["lon"] = dealer["geo"]["longitude"]
            item["phone"] = dealer["telephone"]
            item["website"] = dealer.get("url")
            # Service points are named "MG-servicepunt"; the page gives no other sales/service flag.
            if "servicepunt" in dealer["name"].lower():
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                apply_category(Categories.SHOP_CAR, item)
            yield item
