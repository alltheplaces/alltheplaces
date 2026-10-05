import csv
import gzip
import json
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import clean_address
from locations.searchable_points import get_searchable_points_path
from locations.user_agents import BROWSER_DEFAULT

GAMESTOP_SHARED_ATTRIBUTES = {
    "brand": "GameStop",
    "brand_wikidata": "Q202210",
    "extras": Categories.SHOP_VIDEO_GAMES.value,
}

NAME_CLEANUP_RE = re.compile(r"(?i)\s*-\s*gamestop\b")

UNIT_REPLACEMENTS = (
    (re.compile(r"(?i)\b(?:STE\.?|SUITE)(?=\s|$)"), "Suite"),
    (re.compile(r"(?i)\b(?:SPC[E]?\.?|SPACE)(?=\s|$)"), "Space"),
    (re.compile(r"(?i)\b(?:BLD[G]?\.?|BUILDING)(?=\s|$)"), "Building"),
    (re.compile(r"(?i)\b(?:RM\.?|ROOM)(?=\s|$)"), "Room"),
    (re.compile(r"(?i)\bUNIT(?=\s|$)"), "Unit"),
)


class GamestopUSSpider(Spider):
    name = "gamestop_us"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES
    allowed_domains = ["www.gamestop.com"]
    start_urls = ["https://www.gamestop.com/on/demandware.store/Sites-gamestop-us-Site/default/Stores-FindStores"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
    }

    # Demandware API maximum query radius (in miles)
    api_search_radius_miles: str = "200"

    # Centroid search grid radius in kilometers.
    # Default is 158 km (~98 miles), which maps to 214 search postal codes.
    # When combined with GameStop's 200-mile query radius, this provides 100% US coverage
    # with a ~100-mile overlap safety margin.
    radius_km: int = 158

    def __init__(self, *args: Any, radius_km: int | str = 158, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.radius_km = int(radius_km)

    @staticmethod
    def get_centroid_postal_regions(radius_km: int = 158) -> list[str]:
        """
        Derive the minimal set of search postal codes required for 100% US coverage.
        Because GameStop requires searching by postal code rather than raw coordinates,
        this maps WGS84 ISEADGG geodesic centroids to their nearest US zip code.
        """
        with gzip.open(get_searchable_points_path("postcodes/uszips.csv.gz"), mode="rt", encoding="utf-8") as f:
            zips = [(row["zip"], float(row["lat"]), float(row["lng"])) for row in csv.DictReader(f)]

        mapped = []
        for lat, lon in country_iseadgg_centroids("US", radius_km):
            nearest = min(zips, key=lambda z: (z[1] - lat) ** 2 + (z[2] - lon) ** 2)
            mapped.append(nearest[0])

        return list(dict.fromkeys(mapped))

    async def start(self) -> AsyncIterator[FormRequest]:
        postal_codes = self.get_centroid_postal_regions(self.radius_km)
        self.logger.info(
            "Starting crawl with %d centroid-derived postal codes (grid radius: %d km)",
            len(postal_codes),
            self.radius_km,
        )
        for url in self.start_urls:
            for postcode in postal_codes:
                yield FormRequest(
                    url=url,
                    method="POST",
                    headers={"Referer": "https://www.gamestop.com/stores/"},
                    formdata={"radius": self.api_search_radius_miles, "postalCode": postcode},
                )

    @staticmethod
    def parse_hours(item: Feature, raw_hours: str | None) -> None:
        if not raw_hours or not (hours := json.loads(raw_hours)):
            return
        if all(day["open"] == "CLOSED" and day["close"] == "CLOSED" for day in hours):
            # Stores pending closure report every day as CLOSED.
            set_closed(item)
            return
        item["opening_hours"] = OpeningHours()
        for day in hours:
            item["opening_hours"].add_range(day["day"], day["open"], day["close"], "%H%M")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["name"] = NAME_CLEANUP_RE.sub("", item["name"]).strip()
            item["website"] = f"https://www.gamestop.com/search/?store={item['ref']}"
            if addr2 := location.get("address2"):
                for pattern, repl in UNIT_REPLACEMENTS:
                    addr2 = pattern.sub(repl, addr2)
                item["street_address"] = clean_address([location.get("address1"), addr2])
            self.parse_hours(item, location.get("storeOperationHours"))

            yield item
