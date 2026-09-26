import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The locations page is a Next.js app whose page data holds every restaurant,
# with the address split into lines, coordinates, phone and a per day hours
# list.
#
# Those hours are free text and vary between restaurants: "11:00am - 12:00am",
# "11am - 11pm", "11:00am - Midnight" and so on.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class EurekaUSSpider(Spider):
    name = "eureka_us"
    item_attributes = {"brand": "Eureka!"}
    allowed_domains = ["eurekarestaurantgroup.com"]
    start_urls = ["https://eurekarestaurantgroup.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (page_data := response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()):
            self.logger.error("No page data on the locations page")
            return

        for entry in json.loads(page_data)["props"]["pageProps"]["data"]:
            location = entry["data"]["data"]
            if location.get("opening_soon"):
                continue

            item = Feature()
            item["ref"] = f"{location['name']}-{location['zip']}"
            item["branch"] = location.get("name")
            item["street_address"] = merge_address_lines(
                [location.get("address_line_1"), location.get("address_line_2"), location.get("address_line_3")]
            )
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("zip")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            item["phone"] = location.get("phone")

            item["opening_hours"] = self.parse_opening_hours(location.get("hours") or [])

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "burger"

            yield item

    @staticmethod
    def parse_opening_hours(hours: list[dict]) -> OpeningHours | None:
        """Each entry is {"day": "Monday", "store_hours": "11:00am - 12:00am"}."""
        oh = OpeningHours()

        for rule in hours:
            if not (day := DAYS_EN.get((rule.get("day") or "").strip())):
                continue

            times = (rule.get("store_hours") or "").replace("\u2013", "-")
            times = re.sub(r"(?i)midnight", "12:00am", times)
            if not (
                match := re.search(
                    r"(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)", times, re.I
                )
            ):
                continue

            oh.add_range(
                day,
                EurekaUSSpider.normalise_time(match.group(1)),
                EurekaUSSpider.normalise_time(match.group(2)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").replace(".", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
