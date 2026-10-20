import re
from functools import lru_cache
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature

# Local-language "branch"/"office"/"service point" wording (and the legal-entity prefix) removed from
# branch labels so only the distinguishing part remains.
BRANCH_NOISE = re.compile(
    r"\b(as\s+citadele\s+banka|fili(?:āle|aal|alas)|skyrius|"
    r"klientu apkalpošanas centrs|mobilās apkalpošanas punkts)\b",
    re.IGNORECASE,
)
# "(contactless)" service suffix on ATM names in the three languages; already captured by payment:contactless.
CONTACTLESS = re.compile(r"\s*\((?:bekontaktis|bezkontaktai|bezkontakta|kontaktivaba)\)\s*$", re.IGNORECASE)


@lru_cache
def baltic_cities() -> list[tuple[float, float, str]]:
    return [
        (float(city["latitude"]), float(city["longitude"]), cc.upper())
        for cc in ("ee", "lt", "lv")
        for city in city_locations(cc)
    ]


class CitadeleEELTLVSpider(Spider):
    name = "citadele_ee_lt_lv"
    item_attributes = {"brand": "Citadele bank", "brand_wikidata": "Q14239556"}

    async def start(self) -> AsyncIterator[Any]:
        # Every national site serves the same pan-Baltic list, localised to its own language and with no
        # per-location country. Each site is crawled and only its own country's locations are kept (see
        # parse), so every POI keeps a native-language name and gets the correct country.
        for country, language in {"ee": "et", "lt": "lt", "lv": "lv"}.items():
            yield Request(url=f"https://www.citadele.{country}/{language}/map/", cb_kwargs={"country": country.upper()})

    def parse(self, response: Response, country: str, **kwargs: Any) -> Any:
        # Source is HTML (locations sit in <li> data-* attributes) so fields are read with XPath rather
        # than DictParser, which targets JSON/dict sources.
        for location in response.xpath('//li[contains(@class, "location-details")]'):
            lat = float(location.xpath("@data-latitude").get())
            lon = float(location.xpath("@data-longitude").get())
            if self.nearest_country(lat, lon) != country:
                continue  # a foreign location localised into this site's language; kept from its own site

            name = location.xpath('normalize-space(.//h3[@class="title"])').get()

            item = Feature(ref=location.xpath("@data-id").get(), lat=lat, lon=lon, country=country)
            item["addr_full"] = location.xpath('normalize-space(.//p[@class="address"])').get()

            if location.xpath("@data-type").get() == "branch":
                if "leasing" in name.casefold():
                    continue  # Citadele Leasing offices provide only leasing services, not banking
                item["branch"] = self.clean_branch(name)
                apply_category(Categories.BANK, item)
            else:
                options = (location.xpath("@data-options").get() or "").split()
                apply_yes_no(Extras.CASH_IN, item, "cash_deposit_atm" in options)
                apply_yes_no(
                    PaymentMethods.CONTACTLESS, item, "contactless_atm" in options or bool(CONTACTLESS.search(name))
                )
                venue = CONTACTLESS.sub("", name)
                if "citadele" not in venue.casefold():  # drop "at the Citadele branch" style brand-only labels
                    item["name"] = venue
                apply_category(Categories.ATM, item)

            yield item

    @staticmethod
    def clean_branch(name: str) -> str | None:
        branch = BRANCH_NOISE.sub("", name).strip(' "“”„-')
        return None if branch.casefold() == "citadele" else branch or None

    @staticmethod
    def nearest_country(lat: float, lon: float) -> str:
        return min(baltic_cities(), key=lambda city: (lat - city[0]) ** 2 + (lon - city[1]) ** 2)[2]
