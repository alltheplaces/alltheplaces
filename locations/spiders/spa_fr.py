import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# Each service at a site (shelter, pound, vet clinic, youth club...) is a separate API row.
# Fourrières always duplicate a co-located Refuge and Clubs jeunes carry no real data of their
# own, so both are dropped here, along with the head office and unfiltered rows.
CATEGORY_TAGS = {
    "Refuges": {"amenity": "animal_shelter"},
    "Dispensaires": {"amenity": "veterinary"},
    "Maisons SPA": {"office": "association"},
}

BRAND_PREFIX = re.compile(
    r"^la\s+(société protectrice des animaux\s*(\(la\s*spa\)|\(spa\))?|spa)\s*[-–]\s*",
    re.IGNORECASE,
)


class SpaFRSpider(Spider):
    name = "spa_fr"
    item_attributes = {"brand": "SPA", "brand_wikidata": "Q47391644", "name": "SPA"}
    allowed_domains = ["www.la-spa.fr"]
    start_urls = ["https://www.la-spa.fr/app/wp-json/spa/v1/establishments"]
    # robots.txt disallows /app/wp-json/*, which is the only path serving establishment data.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response) -> Any:
        for location in response.json()["items"]:
            category = CATEGORY_TAGS.get((location.get("filter") or {}).get("name"))
            if category is None:
                continue
            yield JsonRequest(
                url=f"https://www.la-spa.fr/app/wp-json/spa/v2/establishments/{location['ID']}",
                callback=self.parse_item,
                errback=self.parse_item_error,
                cb_kwargs={"category": category, "fallback": location},
            )

    def parse_item(self, response: Response, category: dict, fallback: dict) -> Any:
        location = response.json()
        item = DictParser.parse(location)
        item["ref"] = location["id"]
        item["street_address"] = item.pop("addr_full", None)
        # The detail endpoint occasionally has a blank name for a valid record; the list
        # endpoint always has one.
        raw_name = item.pop("name", None) or fallback.get("name") or ""
        item["branch"] = BRAND_PREFIX.sub("", raw_name).strip()
        item["website"] = response.urljoin(location["url"])
        apply_category(category, item)
        if (has_pmr := location.get("hasAccessPmr")) is not None:
            apply_yes_no(Extras.WHEELCHAIR, item, has_pmr, False)
        if (has_parking := location.get("hasParking")) is not None:
            apply_yes_no(Extras.PARKING, item, has_parking, False)

        oh = OpeningHours()
        for day, day_ranges in (location.get("openingHours") or {}).items():
            for r in day_ranges:
                oh.add_range(
                    day, f"{r['startHour']:02d}:{r['startMinute']:02d}", f"{r['endHour']:02d}:{r['endMinute']:02d}"
                )
        item["opening_hours"] = oh

        yield item

    def parse_item_error(self, failure):
        # spa/v2/establishments/{id} intermittently 500s on specific IDs (e.g.
        # Cabourg, id 7362) - fall back to the v1 list row rather than losing
        # the POI. No structured opening hours available on this path.
        category = failure.request.cb_kwargs["category"]
        location = failure.request.cb_kwargs["fallback"]
        item = DictParser.parse(location)
        item["ref"] = location["ID"]
        item["street_address"] = (item.pop("addr_full", None) or "").replace("<br>", ", ")
        item["branch"] = BRAND_PREFIX.sub("", item.pop("name", None) or "").strip()
        item["website"] = f"https://www.la-spa.fr{location['url']}"
        apply_category(category, item)
        yield item
