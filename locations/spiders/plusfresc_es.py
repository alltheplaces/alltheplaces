import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

# Province name (last line of the source address, with the trailing country
# name stripped) to ISO 3166-2 state code.
STATE_CODES = {
    "lleida": "ES-L",
    "barcelona": "ES-B",
    "tarragona": "ES-T",
    "zaragoza": "ES-Z",
}


class PlusfrescESSpider(Spider):
    name = "plusfresc_es"
    item_attributes = {"brand": "Plusfresc", "brand_wikidata": "Q111373081", "name": "Plusfresc"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://www.plusfresc.cat/wp-json/plusfresc-api/v1/shops")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        seen_coordinates = set()

        for shop in response.json().get("shops", []):
            # A handful of listings (e.g. "SUNKA") are a different, related
            # banner sharing this API, not the Plusfresc brand itself.
            if not shop.get("shop_name", "").strip().startswith("Plusfrésc"):
                continue

            item = Feature()
            item["ref"] = shop.get("shop_id")
            item["branch"] = re.sub(r"^Plusfrésc:\s*", "", shop["shop_name"]).strip()

            coordinates = (shop.get("latitude"), shop.get("longitude"))
            if coordinates == (1.0, 1.0):
                pass  # obvious placeholder value, not a real location
            elif coordinates in seen_coordinates:
                pass  # exact duplicate of another shop's coordinates, not trustworthy
            else:
                seen_coordinates.add(coordinates)
                item["lat"], item["lon"] = coordinates

            self.parse_address(item, shop.get("address") or "")
            item["country"] = "ES"

            apply_category(Categories.SHOP_SUPERMARKET, item)
            apply_yes_no(Extras.WIFI, item, shop.get("has_wifi"))

            yield item

    @staticmethod
    def parse_address(item: Feature, address: str) -> None:
        lines = [line.strip() for line in address.split("\n") if line.strip()]
        if not lines:
            return

        item["street_address"] = lines[0]

        if len(lines) < 3:
            return

        # The address is generally three lines (street; postcode + city;
        # province + country), though a few listings repeat the city name
        # on its own line before the postcode line.
        postcode_city = lines[-2]
        province_country = lines[-1]

        if m := re.match(r"^(\d{5})\s+(.+)$", postcode_city):
            item["postcode"], item["city"] = m.groups()

        province = re.sub(r"\s*espa[ñn]a\s*$", "", province_country, flags=re.IGNORECASE).strip()
        item["state"] = STATE_CODES.get(province.lower())
