import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Location pages come from the WordPress page sitemap. Each is built with
# Elementor and gives the branch as a heading, then a text block holding the
# hours, phone and address, one line at a time.
#
# No coordinates are published: the directions button links to a Google Maps
# place page for the address, without an "@lat,lng" part.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})")
# A line of hours starts with a day or a range of days, however abbreviated.
HOURS_LINE = re.compile(r"(?i)^(hours|[a-z]{1,9}(\s*-\s*[a-z]{1,9})?\s*:)")
DAYS = {
    "M": "Mo",
    "MON": "Mo",
    "T": "Tu",
    "TU": "Tu",
    "TUE": "Tu",
    "W": "We",
    "WED": "We",
    "TH": "Th",
    "THU": "Th",
    "THUR": "Th",
    "F": "Fr",
    "FRI": "Fr",
    "SA": "Sa",
    "SAT": "Sa",
    "SU": "Su",
    "SUN": "Su",
}


class EastBayDeliUSSpider(SitemapSpider):
    name = "east_bay_deli_us"
    item_attributes = {"brand": "East Bay Deli"}
    allowed_domains = ["www.eastbaydeli.com"]
    sitemap_urls = ["https://www.eastbaydeli.com/page-sitemap.xml"]
    sitemap_rules = [(r"/location/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for block in response.xpath('//div[contains(@class, "elementor-widget-text-editor")]'):
            lines = [re.sub(r"\s+", " ", line).strip() for line in block.xpath(".//text()").getall() if line.strip()]
            address = next((line for line in lines if ADDRESS.fullmatch(line)), None)
            if not address:
                continue

            item = Feature()
            item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
            # The heading above the block names the branch on most pages, but is
            # marketing copy on one, so a long or punctuated value falls back to
            # the page slug.
            branch = re.sub(
                r"\s+",
                " ",
                block.xpath('./preceding::*[contains(@class, "elementor-heading-title")][1]//text()').get("") or "",
            ).strip()
            branch = re.sub(r"(?i)^east bay deli\s*[-\u2013]?\s*", "", branch)
            if not branch or len(branch) > 40 or "," in branch:
                branch = item["ref"].replace("-", " ").title()
            item["branch"] = branch
            item["website"] = response.url
            item["city"], item["state"], item["postcode"] = ADDRESS.fullmatch(address).groups()
            # The street can run across two lines before the city line, and
            # the block also carries the hours and the phone.
            street = []
            for line in lines[: lines.index(address)]:
                if re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", line):
                    continue
                if HOURS_LINE.match(line):
                    continue
                street.append(line)
            item["street_address"] = ", ".join(street[-2:]) if street else None

            item["phone"] = next(
                (
                    phone.group(0)
                    for line in lines
                    if (phone := re.fullmatch(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", line.strip()))
                ),
                None,
            )

            item["opening_hours"] = self.parse_opening_hours(lines)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "sandwich"

            yield item
            return

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The hours read "Daily: 8AM - 8PM", or a day range such as "Mon-Sat: ..."."""
        oh = OpeningHours()

        for line in lines:
            line = line.replace("\u2013", "-").replace("\u2014", "-")
            if not (rule := re.fullmatch(r"([A-Za-z]{1,9})\s*(?:-\s*([A-Za-z]{1,9}))?\s*:\s*(.+)", line)):
                continue

            if rule.group(1).lower() == "daily":
                days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
            else:
                # Days are abbreviated inconsistently, down to "M-F" and "SAT".
                start = DAYS.get(rule.group(1).upper()) or sanitise_day(rule.group(1))
                end = DAYS.get((rule.group(2) or rule.group(1)).upper()) or sanitise_day(rule.group(2) or "")
                if not start or not end:
                    continue
                days = day_range(start, end)

            if "closed" in rule.group(3).lower():
                for day in days:
                    oh.set_closed(day)
                continue

            if times := re.fullmatch(
                r"\s*(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)\s*", rule.group(3), re.I
            ):
                oh.add_days_range(
                    days,
                    EastBayDeliUSSpider.normalise_time(times.group(1)),
                    EastBayDeliUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
