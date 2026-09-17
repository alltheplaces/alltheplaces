import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Every restaurant is a block on the one locations page, with the address
# inside a map link and the hours as a short list of "<days> <times>" lines.
#
# Half the blocks link to maps.google.com, which carries the coordinates, and
# half to a goo.gl short link, which does not, so only some features have
# geometry.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BakersfieldUSSpider(Spider):
    name = "bakersfield_us"
    item_attributes = {"brand": "Bakersfield"}
    allowed_domains = ["www.bakersfieldtacos.com"]
    start_urls = ["https://www.bakersfieldtacos.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[@class="location"]'):
            # Some blocks link the address to maps.google.com and some to a
            # goo.gl short link.
            address_link = location.xpath('.//p//a[contains(@href, "maps")]')
            lines = [text.strip() for text in address_link.xpath(".//text()").getall() if text.strip()]
            # "Cincinnati, OH 45202", and on one block "Nashville TN 37201".
            if len(lines) < 2 or not (locality := re.fullmatch(r"(.+?),?\s+([A-Z]{2})\s+(\d{5})", lines[-1])):
                continue

            item = Feature()
            item["branch"] = (location.xpath(".//h2/text()").get() or "").strip()
            item["ref"] = item["branch"]
            item["street_address"] = " ".join(lines[:-1]).rstrip(",")
            item["city"], item["state"], item["postcode"] = [group.strip() for group in locality.groups()]
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/text()').get()
            item["website"] = response.url

            # Only the full maps links carry coordinates; the short links
            # would need to be resolved.
            if coordinates := re.search(
                r"/@(-?\d+\.\d+),(-?\d+\.\d+)", unquote(address_link.xpath("@href").get() or "")
            ):
                item["lat"], item["lon"] = coordinates.groups()

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "mexican;tacos"

            yield item

    @staticmethod
    def parse_opening_hours(location: Selector) -> OpeningHours | None:
        """Parses lines such as "Mon-Thurs 11AM-11PM" and "Fri-Sat 11AM-12AM"."""
        oh = OpeningHours()

        for line in location.xpath('.//ul[@class="list-unstyled"]/li/text()').getall():
            line = line.replace("\u2013", "-").replace("\u2014", "-").strip()
            if not (
                times := re.search(r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", line, re.I)
            ):
                continue

            day_names = []
            for token in re.split(r"&|\band\b", line[: times.start()].strip(" :")):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        day_names.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    day_names.append(day)

            if day_names:
                oh.add_days_range(
                    day_names,
                    BakersfieldUSSpider.normalise_time(times.group(1)),
                    BakersfieldUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").lower()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
