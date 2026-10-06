import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page gives each restaurant a Divi section holding its name, a
# Google Maps embed whose URL carries the coordinates, and blurbs for the
# address, phone and hours.
#
# The first section on the page is an overview listing every address, so a
# section is only read when it names a single restaurant.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class SwadleysBbqUSSpider(Spider):
    name = "swadleys_bbq_us"
    item_attributes = {"brand": "Swadley's Bar-B-Q"}
    allowed_domains = ["swadleys.com"]
    start_urls = ["https://swadleys.com/swadleys-locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for section in response.xpath(
            '//div[contains(@class, "et_pb_section")][.//iframe[contains(@src, "maps/embed")]]'
        ):
            blurbs = [
                re.sub(r"\s+", " ", " ".join(blurb.xpath(".//text()").getall())).strip()
                for blurb in section.xpath('.//h5[contains(@class, "et_pb_module_header")]')
            ]
            addresses = [match for blurb in blurbs if (match := ADDRESS.fullmatch(blurb))]
            # The overview section lists every restaurant's address.
            if len(addresses) != 1:
                continue

            heading = next(
                (
                    re.sub(r"\s+", " ", head).strip()
                    for head in section.xpath(".//h2//text() | .//h3//text()").getall()
                    if "swadley" in head.lower()
                ),
                "",
            )

            item = Feature()
            item["branch"] = re.sub(r"(?i)^swadley.s\s*", "", heading).strip() or None
            item["street_address"], item["city"], item["state"], item["postcode"] = addresses[0].groups()
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{item['branch']} {item['postcode']}".lower()).strip("-")

            lines = [
                re.sub(r"\s+", " ", line).strip() for line in section.xpath(".//text()").getall() if line.strip()
            ]
            if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
                item["phone"] = phone.group(0)

            # "!2d-97.166365!3d34.190266" in the Google Maps embed URL.
            embed = section.xpath('.//iframe[contains(@src, "maps/embed")]/@src').get("")
            if longitude := re.search(r"!2d(-?\d+\.\d+)", embed):
                item["lon"] = longitude.group(1)
            if latitude := re.search(r"!3d(-?\d+\.\d+)", embed):
                item["lat"] = latitude.group(1)

            apply_yes_no(Extras.DRIVE_THROUGH, item, "drive-thru" in " ".join(lines).lower(), False)

            item["opening_hours"] = self.parse_opening_hours(lines)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "barbecue"

            yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The hours read "Hours - Mon - SAT" then "7:00 AM - 9:00 PM"."""
        oh = OpeningHours()

        for label, hours in zip(lines, lines[1:]):
            text = f"{label} {hours}".replace("\u2013", "-").replace("\u2014", "-")
            if not re.match(r"(?i)\s*hours", label):
                continue
            for rule in re.finditer(
                r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\.?\s*:?\s*"
                r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)",
                text,
                re.I,
            ):
                start, end = sanitise_day(rule.group(1)), sanitise_day(rule.group(2) or rule.group(1))
                if not start or not end:
                    continue
                oh.add_days_range(
                    day_range(start, end),
                    SwadleysBbqUSSpider.normalise_time(rule.group(3)),
                    SwadleysBbqUSSpider.normalise_time(rule.group(4)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
