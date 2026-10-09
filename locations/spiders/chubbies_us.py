import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The stores page is a Shopify page whose stores are plain text blocks: the
# branch in one block, then the address, phone and hours as lines of the next.
#
# One store wraps its address across two lines, and the hours are written with
# or without spaces around the dash.
#
# No coordinates are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class ChubbiesUSSpider(Spider):
    name = "chubbies_us"
    item_attributes = {"brand": "Chubbies"}
    allowed_domains = ["www.chubbiesshorts.com"]
    start_urls = ["https://www.chubbiesshorts.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        branch = None

        for block in response.xpath('//div[contains(@class, "_markdown_")]'):
            for paragraph in block.xpath("./p"):
                lines = [
                    re.sub(r"\s+", " ", line).strip()
                    for line in paragraph.xpath("./text() | ./*[not(self::br)]//text()").getall()
                ]
                lines = [line for line in lines if line]
                if not lines:
                    continue

                # The address block follows the branch block.
                joined = " ".join(lines)
                if not (address := ADDRESS.search(joined)):
                    branch = lines[0] if len(lines) == 1 else branch
                    continue
                if not branch:
                    continue

                item = Feature()
                item["branch"] = branch.title() if branch.isupper() else branch
                item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
                item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{branch} {item['postcode']}".lower()).strip("-")
                if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
                    item["phone"] = phone.group(0)

                item["opening_hours"] = self.parse_opening_hours(lines)

                apply_category(Categories.SHOP_CLOTHES, item)

                branch = None
                yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The hours read "Mon-Sat: 10AM - 8PM" or "Mon-Thu: 10AM-8PM"."""
        oh = OpeningHours()

        for line in lines:
            line = line.replace("\u2013", "-").replace("\u2014", "-")
            if not (
                rule := re.fullmatch(
                    r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\s*:\s*"
                    r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)",
                    line,
                    re.I,
                )
            ):
                continue

            start, end = sanitise_day(rule.group(1)), sanitise_day(rule.group(2) or rule.group(1))
            if not start or not end:
                continue

            oh.add_days_range(
                day_range(start, end),
                ChubbiesUSSpider.normalise_time(rule.group(3)),
                ChubbiesUSSpider.normalise_time(rule.group(4)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
