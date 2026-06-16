import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature


class BabyWalzDESpider(Spider):
    """Spider for Baby-walz baby goods stores (DE, AT, CH).
    Closes #7075
    """

    name = "baby_walz_de"
    item_attributes = {"brand": "baby-walz", "brand_wikidata": "Q108004413"}
    start_urls = ["https://www.baby-walz.de/filialen/"]

    # RSC pattern: lat, lon, "email@domain", "https://maps.url", ...
    _STORE_RE = re.compile(
        r",(-?\d+\.\d{4,}),(-?\d+\.\d{4,}),"
        r'"([^"]+@baby-walz\.[a-z]+)",'
        r'"(https://www\.google\.[a-z]+/maps/[^"]+)",'
    )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        seen = set()
        for m in self._STORE_RE.finditer(response.text):
            lat, lon, email, maps_url = m.groups()

            if email in seen:
                continue
            seen.add(email)

            # derive slug from email local part e.g. "badwaldsee@baby-walz.de"
            slug = email.split("@")[0]
            country = email.split(".")[-1].upper()
            if country == "COM":
                country = "DE"

            # extract coords from Google Maps URL (more precise than RSC values)
            map_lat, map_lon = url_to_coords(maps_url)
            if not map_lat:
                map_lat, map_lon = float(lat), float(lon)

            # extract address from maps URL
            addr = ""
            addr_m = re.search(r"//([^/@]+)/@", maps_url)
            if addr_m:
                addr = unquote(addr_m.group(1)).replace("+", " ")

            item = Feature()
            item["ref"] = slug
            item["branch"] = slug.replace("-", " ").title()
            item["addr_full"] = addr or None
            item["email"] = email
            item["country"] = country
            item["lat"] = map_lat
            item["lon"] = map_lon

            apply_category(Categories.SHOP_BABY_GOODS, item)
            yield item
