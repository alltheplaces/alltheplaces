import json
import re
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy.http import Request, TextResponse
from scrapy.settings.default_settings import RETRY_HTTP_CODES

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

COUNTRIES = {
    "www.king-jouet.com": "FR",
    "www.king-jouet.be": "BE",
    "www.king-jouet.ch": "CH",
    "www.king-jouet.lu": "LU",
}
OVERSEAS_POSTCODE_PREFIXES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT", "987": "PF", "988": "NC"}


class KingJouetSpider(JSONBlobSpider):
    name = "king_jouet"
    item_attributes = {"brand": "King Jouet", "brand_wikidata": "Q3197009", "name": "King Jouet"}
    # king-jouet.com/magasins/ only links to department pages; the other sites list every store on it.
    start_urls = [f"https://{domain}/magasins/" for domain in COUNTRIES]
    custom_settings = {
        # robots.txt is DataDome-blocked and fetched before spider code can attach zyte_api meta.
        "ROBOTSTXT_OBEY": False,
        # Zyte occasionally returns a 304 redirect to the homepage for a valid page; a retry gets it.
        "RETRY_HTTP_CODES": RETRY_HTTP_CODES + [304],
        # The default policy gave up on a whole country page after 4 DataDome bans (520).
        "ZYTE_API_RETRY_POLICY": "zyte_api.aggressive_retrying",
    }

    def zyte_request(self, url: str, **kwargs) -> Request:
        # Without httpResponseHeaders, scrapy-zyte-api returns a plain Response (no selectors).
        zyte_api = {
            "httpResponseBody": True,
            "httpResponseHeaders": True,
            "geolocation": COUNTRIES[urlparse(url).netloc],
        }
        return Request(url, meta={"zyte_api": zyte_api}, **kwargs)

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield self.zyte_request(url)

    def parse(self, response: TextResponse) -> Iterable[Feature | Request]:
        for url in response.xpath('//a[contains(@href, "/touslesmagasins.htm")]/@href').getall():
            yield self.zyte_request(response.urljoin(url))
        yield from super().parse(response)

    def extract_json(self, response: TextResponse) -> list[dict]:
        if not (nuxt_data := response.xpath('//script[@id="__NUXT_DATA__"]/text()').get()):
            self.logger.warning(f"No __NUXT_DATA__ payload on {response.url}")
            return []
        payload = json.loads(nuxt_data)
        store_keys = {"guid", "code", "label", "latitude", "longitude", "openingHours", "slug"}
        return [
            self.resolve(payload, index)
            for index, node in enumerate(payload)
            if isinstance(node, dict) and store_keys <= node.keys()
        ]

    def resolve(self, payload: list, index: Any, seen: tuple[int, ...] = ()) -> Any:
        # Nuxt 3's flat, index-referenced "__NUXT_DATA__" payload. See wilco_farm_us.py.
        if not isinstance(index, int) or not (0 <= index < len(payload)) or index in seen:
            return None if isinstance(index, int) else index
        node = payload[index]
        seen = seen + (index,)
        if isinstance(node, dict):
            return {key: self.resolve(payload, child, seen) for key, child in node.items()}
        if isinstance(node, list):
            return [self.resolve(payload, child, seen) for child in node]
        return node

    def post_process_item(self, item: Feature, response: TextResponse, store: dict) -> Iterable[Feature]:
        # King'Dultes (collectibles) and King Okaz (second-hand toys) are separate concepts, not toy shops.
        if any(banner in (store.get("label") or "").upper() for banner in ("DULTES", "OKAZ")):
            return
        # The Papeete store has no code, and its store page (built from the code) is broken.
        item["ref"] = store.get("code") or store["guid"]
        if store.get("code"):
            item["website"] = response.urljoin(f"/magasins/{store['slug']}")
        # Drop the brand and store-format prefixes; "CITY 2" is a Brussels shopping centre, not the format.
        item["branch"] = re.sub(
            r"^(?:KING JOUET |CITY (?!\d)|BOUTIQUE )+", "", (store.get("label") or "").strip(), flags=re.I
        )
        item["country"] = OVERSEAS_POSTCODE_PREFIXES.get(
            (store.get("postalCode") or "")[:3], COUNTRIES[urlparse(response.url).netloc]
        )

        oh = OpeningHours()
        for day in store.get("openingHours") or []:
            weekday = DAYS[(day["day"] - 1) % 7]
            for period in (day.get("openingHoursPeriod1"), day.get("openingHoursPeriod2")):
                if not period:
                    continue
                if period.strip().lower() in CLOSED_FR:
                    oh.set_closed(weekday)
                else:
                    # Mostly "10h00 - 12h30", occasionally "10:00 - 16:00".
                    open_time, close_time = period.replace("h", ":").split(" - ")
                    oh.add_range(weekday, open_time.strip(), close_time.strip())
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_TOYS, item)
        yield item
