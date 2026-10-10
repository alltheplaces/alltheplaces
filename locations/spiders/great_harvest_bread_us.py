import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature

# The bakery finder is served by Blipstar. Its searchdbnew endpoint returns
# every US bakery in one response when asked for a large enough page, with the
# first element of the array being a header rather than a bakery.
#
# Addresses arrive as one string and hours as a field per day, written as
# "7AM-6PM" or "CLOSED".


class GreatHarvestBreadUSSpider(Spider):
    name = "great_harvest_bread_us"
    item_attributes = {"brand": "Great Harvest Bread Company", "brand_wikidata": "Q5599297"}
    allowed_domains = ["viewer.blipstar.com"]
    start_urls = [
        "https://viewer.blipstar.com/searchdbnew"
        "?uid=600237&lat=999&lng=999&type=all&value=10&keyword=&sp=&son=&product=&product2="
        "&cnt=us&mb=false&state=&start=0&show=500"
    ]

    def start_requests(self) -> Iterable[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            # The first element carries the result counts.
            if "bpid" not in location:
                continue

            item = Feature()
            item["ref"] = location["bpid"]
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["phone"] = location.get("p")
            item["website"] = f"https://www.greatharvest.com/{location['pr']}" if location.get("pr") else None

            # "Metro Mall, 570 E. Benson, Anchorage, AK 99503", with the state
            # and postcode variously separated by a space or a comma, sometimes
            # repeated, and sometimes with a trailing full stop on a part.
            if address := re.match(
                r"(?P<street>.+?),\s*(?P<city>[^,]+?)\.?,\s*(?P<state>[A-Z]{2}),?\s+(?P<postcode>\d{5})",
                re.sub(r"\s+", " ", (location.get("ad") or "").strip()),
            ):
                item["street_address"] = address["street"]
                item["city"] = address["city"]
                item["state"] = address["state"]
                item["postcode"] = address["postcode"]
            else:
                item["addr_full"] = location.get("ad")

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.SHOP_BAKERY, item)

            yield item

    @staticmethod
    def parse_opening_hours(location: dict) -> OpeningHours | None:
        """Reads the per day fields, each "7AM-6PM", "6:30AM - 6PM" or "CLOSED"."""
        oh = OpeningHours()

        for day, field in zip(DAYS_3_LETTERS, ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
            times = (location.get(field) or "").strip()
            # Some bakeries append a note, e.g. "6AM-5PM Lunch Served Until
            # 4PM", so the opening times are matched at the start of the field.
            if not (
                match := re.match(
                    r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*(?:-|to)\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", times, re.I
                )
            ):
                continue

            oh.add_range(
                day,
                GreatHarvestBreadUSSpider.normalise_time(match.group(1)),
                GreatHarvestBreadUSSpider.normalise_time(match.group(2)),
                time_format="%I:%M%p",
            )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
