import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# Every location is a block on the one locations page, marked up with
# schema.org microdata. Coordinates come from the Google Maps link behind each
# block's "Directions" button.
#
# Franchises that have not opened yet are flagged in the block title, e.g.
# "Lexington (Coming Soon)".
#
# No brand:wikidata is set because the chain has no Wikidata item.


class CurritoUSSpider(Spider):
    name = "currito_us"
    item_attributes = {"brand": "Currito"}
    allowed_domains = ["www.currito.com"]
    start_urls = ["https://www.currito.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[@class="location"]'):
            title = (location.xpath("@data-title").get() or "").strip()
            if "coming soon" in title.lower():
                continue

            item = Feature()
            item["branch"] = title.removesuffix("(Now Open)").strip()
            item["ref"] = item["branch"]
            item["street_address"] = location.xpath('.//*[@itemprop="streetAddress"]/text()').get()
            item["city"] = location.xpath('.//*[@itemprop="addressLocality"]/text()').get()
            item["state"] = location.xpath('.//*[@itemprop="addressRegion"]/text()').get()
            item["postcode"] = location.xpath('.//*[@itemprop="postalCode"]/text()').get()
            item["phone"] = location.xpath('.//*[@itemprop="telephone"]/text()').get()

            extract_google_position(item, location)

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "burrito"

            yield item

    @staticmethod
    def parse_opening_hours(location: Selector) -> OpeningHours | None:
        """Parses rules such as "Mon - Sun: 11am - 9pm"; some blocks omit the colon."""
        oh = OpeningHours()
        for line in location.xpath('.//span[@class="hours"]//p//text()').getall():
            line = line.replace("\u2013", "-").replace("\u2014", "-").strip()
            # Skips the blurb express locations carry in place of hours.
            if not re.search(r"\d\s*[ap]m", line, re.I):
                continue
            oh.add_ranges_from_string(line, days=DAYS_EN)
        return oh if oh.as_opening_hours() else None
