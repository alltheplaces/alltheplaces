import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature

# The locations page groups its restaurants under a heading per city, each
# block giving the street on the first line and usually a phone below it, plus
# a map link whose query sometimes carries the postcode.
#
# Coordinates are not usable: the map links carry an ll or sll parameter, but
# it is the map's default centre and repeats across restaurants.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class RobertosTacoShopUSSpider(Spider):
    name = "robertos_taco_shop_us"
    item_attributes = {"brand": "Roberto's Taco Shop"}
    allowed_domains = ["robertostacoshop.com"]
    start_urls = ["https://robertostacoshop.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[contains(@class, "wpb_text_column")]//h3'):
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in location.xpath(".//text()").getall()
                if line.strip() and line.strip() not in ("|", "View Map", "VIEW MAP", "Order Online", "More Info")
            ]
            lines = [line for line in lines if not line.startswith(("of ", "for "))]
            if not lines:
                continue

            # "HENDERSON, NEVADA"
            heading = (location.xpath("preceding::h4[1]/text()").get() or "").strip()
            if "," not in heading:
                continue
            city, state = [part.strip().title() for part in heading.rsplit(",", 1)]

            item = Feature()
            item["street_address"] = lines[0]
            item["city"] = city
            item["state"] = state
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{lines[0]} {city}".lower()).strip("-")

            link = unquote(location.xpath('.//a[contains(@href, "maps")]/@href').get() or "")
            if postcode := re.search(r"\b(\d{5})\b", link.split("&", 1)[0]):
                item["postcode"] = postcode.group(1)

            for line in lines[1:]:
                if re.fullmatch(r"\d{3}-\d{3}-\d{4}", line):
                    item["phone"] = line
                elif line.lower().startswith("open"):
                    item["opening_hours"] = self.parse_opening_hours(line)
                elif "drive-thru" in line.lower():
                    apply_yes_no(Extras.DRIVE_THROUGH, item, True, False)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "mexican;tacos"

            yield item

    @staticmethod
    def parse_opening_hours(line: str) -> OpeningHours | None:
        """Parses "OPEN 8AM - MIDNIGHT", which applies to every day."""
        line = line.replace("\u2013", "-").replace("\u2014", "-")
        if not (
            times := re.search(
                r"(\d{1,2}(?::\d{2})?\s*[AP]M|MIDNIGHT)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M|MIDNIGHT)", line, re.I
            )
        ):
            return None

        oh = OpeningHours()
        oh.add_days_range(
            ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
            RobertosTacoShopUSSpider.normalise_time(times.group(1)),
            RobertosTacoShopUSSpider.normalise_time(times.group(2)),
            time_format="%I:%M%p",
        )
        return oh

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        if value == "MIDNIGHT":
            return "12:00AM"
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
