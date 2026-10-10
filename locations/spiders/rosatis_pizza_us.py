import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Location pages come from the site's sitemap. They are built with Duda, whose
# map widget carries the coordinates and the address in data attributes.
#
# The hours sit between the address and the phone as free text lines such as
# "Sunday-Thursday: 11:00am-10:00pm".


class RosatisPizzaUSSpider(SitemapSpider):
    name = "rosatis_pizza_us"
    item_attributes = {"brand": "Rosati's", "brand_wikidata": "Q65052579"}
    allowed_domains = ["www.rosatispizza.com"]
    sitemap_urls = ["https://www.rosatispizza.com/sitemap.xml"]
    sitemap_rules = [(r"/location/([^/]+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        location = response.xpath('//div[@data-type="inlineMap"][@data-address]')
        if not location:
            return

        # "1165 W Spring St, South Elgin, IL 60177"
        address = (location[0].xpath("@data-address").get() or "").strip()
        if not (parts := re.fullmatch(r"(.+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})", address)):
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = (response.xpath("//title/text()").get() or "").strip() or None
        item["website"] = response.url
        item["street_address"], item["city"], item["state"], item["postcode"] = parts.groups()
        item["lat"] = location[0].xpath("@data-lat").get()
        item["lon"] = location[0].xpath("@data-lng").get()
        item["phone"] = response.xpath('//*[contains(text(), "PHONE")]/following::text()[normalize-space()][1]').get()

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        """Parses lines such as "Sunday-Thursday: 11:00am-10:00pm"."""
        oh = OpeningHours()

        for line in response.xpath('//div[contains(@class, "dmNewParagraph")]//text()').getall():
            line = re.sub(r"\s+", " ", line).replace("\u2013", "-").strip()
            if not (times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)):
                continue

            days = []
            for token in re.split(r"&|,|\band\b", line[: times.start()].strip(" :")):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        days.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    days.append(day)

            if days:
                oh.add_days_range(
                    days,
                    RosatisPizzaUSSpider.normalise_time(times.group(1)),
                    RosatisPizzaUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
