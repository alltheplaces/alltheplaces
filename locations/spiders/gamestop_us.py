import csv
import gzip
import json
import re
from io import TextIOWrapper
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import clean_address
from locations.searchable_points import get_searchable_points_path
from locations.user_agents import BROWSER_DEFAULT

GAMESTOP_SHARED_ATTRIBUTES = {
    "brand": "GameStop",
    "brand_wikidata": "Q202210",
    "extras": Categories.SHOP_VIDEO_GAMES.value,
}


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

    # Centroid search grid radius in kilometers.
    # Default is 158 km (~98 miles), which maps to 214 search postal codes.
    # When combined with GameStop's 200-mile query radius, this provides 100% US coverage
    # with a ~100-mile overlap safety margin (cutting requests from 638 to 214).
    # Can also be set to 315 km (~195 miles) for a faster 73-point sweep:
    #   scrapy crawl gamestop_us -a radius_km=315
    radius_km: int = 158

    def __init__(self, *args: Any, radius_km: int | str = 158, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.radius_km = int(radius_km)

    @classmethod
    def get_centroid_postal_regions(cls, radius_km: int = 158) -> list[str]:
        """
        Derive the minimal set of search postal codes required for 100% US coverage.
        Because GameStop requires searching by postal code rather than raw coordinates,
        this maps WGS84 ISEADGG geodesic centroids to their nearest US zip code.
        """
        zips = []
        with gzip.open(get_searchable_points_path("postcodes/uszips.csv.gz"), mode="rb") as points:
            for row in csv.DictReader(TextIOWrapper(points)):
                zips.append((row["zip"], float(row["lat"]), float(row["lng"])))

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
                    formdata={"radius": "200", "postalCode": postcode},
                )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["name"] = re.sub(r"(?i)\s*-\s*gamestop\b", "", item["name"]).strip()
            item["website"] = "https://www.gamestop.com/search/?store=" + item["ref"]
            if addr2 := location.get("address2"):
                unit = re.sub(r"(?i)\b(?:STE\.?|SUITE)(?=\s|$)", "Suite", addr2)
                unit = re.sub(r"(?i)\b(?:SPC[E]?\.?|SPACE)(?=\s|$)", "Space", unit)
                unit = re.sub(r"(?i)\b(?:BLD[G]?\.?|BUILDING)(?=\s|$)", "Building", unit)
                unit = re.sub(r"(?i)\b(?:RM\.?|ROOM)(?=\s|$)", "Room", unit)
                unit = re.sub(r"(?i)\bUNIT(?=\s|$)", "Unit", unit)
                item["street_address"] = clean_address([location.get("address1"), unit])
            if hours := json.loads(location.get("storeOperationHours") or "[]"):
                if all(day["open"] == "CLOSED" and day["close"] == "CLOSED" for day in hours):
                    # Stores pending closure report every day as CLOSED.
                    set_closed(item)
                else:
                    item["opening_hours"] = OpeningHours()
                    for day in hours:
                        item["opening_hours"].add_range(day["day"], day["open"], day["close"], "%H%M")

            yield item
