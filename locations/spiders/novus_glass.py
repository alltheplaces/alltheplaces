import html
import re
from collections import Counter
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

MOBILE_ADDRESS_RE = re.compile(r"mobile|p\.?\s?o\.?\s?box", re.I)


def normalise_contact(value: str | None) -> str | None:
    """Normalise punctuation/whitespace so equivalent phone numbers/emails
    (e.g. "13 22 34" vs "132234", "(03) 9873 3088" vs "03 9873 3088") are
    recognised as duplicates even though the raw source strings differ."""
    if not value:
        return None
    return re.sub(r"[^a-z0-9+]", "", value.lower())


class NovusGlassSpider(Spider):
    name = "novus_glass"
    item_attributes = {"brand": "NOVUS Glass", "brand_wikidata": "Q120636586"}

    # The store finder is powered by the "FN Store Locator" WordPress
    # plugin's REST API, which only supports a coordinate + radius search
    # (a plain "list everything" request returns a 400 error, as does
    # lat=0/lng=0, which the API treats as missing). A radius larger than
    # the maximum possible distance between two points on Earth
    # (~20,015 km) guarantees every location is returned regardless of
    # where in the world it is, no matter which coordinate is searched
    # from.
    start_urls = [
        "https://www.novusglass.com/en-us/wp-json/fn-sl/v1/search?lat=39.8&lng=-98.5&radius=20000&perPage=200&page=1"
    ]

    def parse(self, response: Response) -> Iterable[Request]:
        data = response.json()

        self.stores = getattr(self, "stores", [])
        self.stores.extend(data.get("stores", []))

        if data.get("stores") and len(self.stores) < data.get("total", 0):
            page = data.get("pagination", {}).get("page", 1)
            next_url = re.sub(r"page=\d+", f"page={page + 1}", response.url)
            yield Request(next_url, callback=self.parse)
        else:
            yield from self.parse_stores()

    def parse_stores(self) -> Iterable[Feature]:
        # A large share of locations are mobile-only franchise territories
        # that share one franchisee's phone number/email across many
        # differently named "shop" entries. Since that contact info does
        # not identify any specific branch, drop it when shared by more
        # than one location.
        phone_counts = Counter(normalise_contact(store["contact"].get("phone")) for store in self.stores)
        email_counts = Counter(normalise_contact(store["contact"].get("email")) for store in self.stores)

        for store in self.stores:
            item = DictParser.parse(store)
            item["ref"] = str(store["id"])
            item["name"] = html.unescape(store["short_name"]).strip()
            item["website"] = f"https://www.novusglass.com/en-us/shop/{store['short_slug']}"

            # Many locations are mobile-only and have no fixed storefront;
            # the source fills the street address with a placeholder (or a
            # PO box) in that case, which is not a real address.
            if MOBILE_ADDRESS_RE.search(store["address"].get("line1") or ""):
                item.pop("street_address", None)

            if phone_counts[normalise_contact(store["contact"].get("phone"))] > 1:
                item.pop("phone", None)
            if email_counts[normalise_contact(store["contact"].get("email"))] > 1:
                item.pop("email", None)

            if oh := self.parse_hours(store.get("hours")):
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_CAR_REPAIR, item)
            apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, True)

            yield item

    def parse_hours(self, hours: dict | list | None) -> OpeningHours | None:
        if not isinstance(hours, dict):
            return None

        oh = OpeningHours()
        for day, info in hours.get("WeeklySchedule", {}).items():
            if not info.get("IsOpen"):
                continue
            for period in info.get("OpenTimes", []):
                start, end = period.get("From"), period.get("To")
                if not start or not end or start == end:
                    continue
                oh.add_range(day, start, end)
        return oh
