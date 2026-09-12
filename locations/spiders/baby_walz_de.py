import re
from typing import Any, AsyncIterator, Iterable
from urllib.parse import unquote

from scrapy.http import Request, Response
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class BabyWalzDESpider(CamoufoxSpider):
    """Spider for Baby-walz baby goods stores (DE, AT, CH).
    Closes #7075
    """

    name = "baby_walz_de"
    item_attributes = {"brand": "baby-walz", "brand_wikidata": "Q108004413"}
    start_urls = ["https://www.baby-walz.de/filialen/"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        # The Vercel Security Checkpoint on this site runs its verification
        # in a Web Worker before revealing the real page (sometimes via a
        # client-side reload once the worker signals success). The default
        # CAMOUFOX_ABORT_REQUEST blocks every non-document resource, which
        # can prevent that worker script (and its follow-up requests) from
        # ever loading, so the checkpoint never resolves. Allow scripts/xhr/
        # fetch through as well (still blocking images/fonts/media/
        # stylesheets) so the challenge has a chance to complete.
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type
        not in ("document", "script", "xhr", "fetch"),
    }

    # RSC pattern: lat, lon, "email@domain", "https://maps.url", ...
    _STORE_RE = re.compile(
        r",(-?\d+\.\d{4,}),(-?\d+\.\d{4,}),"
        r'"([^"]+@baby-walz\.[a-z]+)",'
        r'"(https://www\.google\.[a-z]+/maps/[^"]+)",'
    )

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(
                url,
                meta={
                    # The checkpoint can take several seconds (and a reload)
                    # to resolve. Wait for the store data to actually be
                    # present in the document rather than returning
                    # whatever the browser has loaded (e.g. still the
                    # checkpoint's placeholder page) immediately.
                    "camoufox_page_methods": [
                        PageMethod(
                            "wait_for_function",
                            "document.documentElement.outerHTML.includes('@baby-walz.')",
                            timeout=30000,
                        )
                    ],
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        seen = set()
        # The site now serialises its RSC payload with JS-escaped slashes
        # (backslash-u002F instead of a literal slash), so undo that before
        # matching URLs.
        page = response.text.replace("\\u002F", "/")
        for m in self._STORE_RE.finditer(page):
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
