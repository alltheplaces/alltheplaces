import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.searchable_points import open_searchable_points

TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?", re.IGNORECASE)


class BeaconRoofingSupplyUSCASpider(Spider):
    name = "beacon_roofing_supply_us_ca"
    allowed_domains = ["site.becn.com"]

    async def start(self) -> AsyncIterator[Request]:
        for points_file in ["us_centroids_100mile_radius.csv", "ca_centroids_100mile_radius.csv"]:
            with open_searchable_points(points_file) as points:
                next(points)
                for point in points:
                    _, lat, lon = point.strip().split(",")
                    yield Request(
                        url=f"https://site.becn.com/site/api-man/StoreLocation?facets=&lat={lat}&long={lon}&range=100"
                    )

    def parse(self, response: Response):
        for result in response.json().get("items", []):
            store = result["storeLocation"]

            item = DictParser.parse(store)
            # No store ID is provided by the API; the overlapping search grid
            # relies on this stable key, derived from the store's own address,
            # to de-duplicate a branch seen from multiple search points.
            item["ref"] = f"{store.get('postalcode')}_{store.get('addressLine1')}"
            item["street_address"] = clean_address([store.get("addressLine1"), store.get("addressLine2")])
            item.pop("addr_full", None)

            if url := store.get("url"):
                item["website"] = url

            # Most branches trade purely as "Beacon". A minority instead trade
            # under a distinct name inherited from a company Beacon acquired
            # (e.g. "Al's Roofing Supply", "General Siding Supply"); these
            # keep their own name and are tagged as operated by, but not
            # branded, Beacon.
            branch_name = (store.get("branchname") or "").strip()
            if branch_name and branch_name != "Beacon Building Products":
                item["name"] = branch_name
                item["operator"] = "Beacon"
                item["operator_wikidata"] = "Q16950815"
            else:
                item["name"] = "Beacon"
                item["brand"] = "Beacon"
                item["brand_wikidata"] = "Q16950815"

            item["opening_hours"] = self.parse_hours(store)

            apply_category(Categories.SHOP_DOITYOURSELF, item)

            yield item

    @staticmethod
    def parse_time(token: str, default_period: str) -> str | None:
        token = token.strip()
        if not token:
            return None
        if not (m := TIME_RE.match(token)):
            return None
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        period = (m.group(3) or default_period).lower().replace(".", "")
        if period.startswith("p") and hour != 12:
            hour += 12
        elif period.startswith("a") and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    @classmethod
    def parse_time_range(cls, hours_string: str) -> tuple[str, str] | None:
        # Strip notes such as "(Monday 5:00 AM opening)" that don't fit the
        # simple open-close range every other branch uses.
        hours_string = re.sub(r"\(.*?\)", "", hours_string).strip()
        if not hours_string or hours_string.lower() == "closed":
            return None
        hours_string = hours_string.replace("–", "-").replace(" to ", "-")
        parts = hours_string.split("-")
        if len(parts) != 2:
            return None
        open_time = cls.parse_time(parts[0], "am")
        close_time = cls.parse_time(parts[1], "pm")
        if not open_time or not close_time:
            return None
        return open_time, close_time

    @classmethod
    def parse_hours(cls, store: dict) -> OpeningHours:
        opening_hours = OpeningHours()

        if mon_fri := cls.parse_time_range(store.get("monFriStoreHours") or ""):
            opening_hours.add_days_range(DAYS[:5], mon_fri[0], mon_fri[1])

        if sat_sun := cls.parse_time_range(store.get("satSunStoreHours") or ""):
            opening_hours.add_days_range(["Sa", "Su"], sat_sun[0], sat_sun[1])

        return opening_hours
