import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

TIME = r"\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?"
# Every market states one range that applies to the whole week, with no days named:
# "Hours: 8 a.m. to 9 p.m."
HOURS = re.compile(rf"Hours:\s*(?P<opens>{TIME})\s*(?:to|[-–])\s*(?P<closes>{TIME})", re.IGNORECASE)
LOCALITY = re.compile(r"^(?P<city>[A-Za-z .'/-]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$")


class EatzisUSSpider(Spider):
    name = "eatzis_us"
    item_attributes = {"brand": "Eatzi's Market & Bakery"}
    start_urls = ["https://eatzis.com/locations/"]

    @staticmethod
    def normalise(time: str) -> str:
        time = re.sub(r"[\s.]", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def hours(self, text: str) -> OpeningHours:
        oh = OpeningHours()
        if not (match := HOURS.search(text)):
            self.logger.warning(f"Unparsed hours: {text!r}")
            return oh
        for day in DAYS_FULL:
            oh.add_range(day, self.normalise(match["opens"]), self.normalise(match["closes"]))
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for card in response.xpath('//div[contains(@class, "locations_location_content")][h2]'):
            item = Feature()
            item["ref"] = card.xpath("@id").get()
            item["branch"] = card.xpath("normalize-space(h2)").get()
            item["website"] = response.url

            contact = card.xpath('.//div[contains(@class, "locations_location_content_contact_info")]')
            for line in contact.xpath('.//p[contains(@class, "red")]/text()').getall():
                line = re.sub(r"\s+", " ", line).strip()
                if locality := LOCALITY.match(line):
                    item["city"] = locality["city"]
                    item["state"] = locality["state"]
                    item["postcode"] = locality["postcode"]
                elif re.match(r"^\d", line):
                    item["street_address"] = line
            item["phone"] = contact.xpath('.//a[starts-with(@href, "tel:")]/text()').get()

            # Only the hours paragraph is read. Each card also carries a holiday block
            # whose dates are years out of date and which marks a day CLOSED, so it
            # must not be taken for the hours the market keeps.
            item["opening_hours"] = self.hours(
                card.xpath('normalize-space(.//p[contains(@class, "locations_location_content_hours")])').get("")
            )

            # The markets sell chef-prepared meals to take away alongside a bakery
            # counter and groceries. No coordinates are published: each address links
            # to a Google place by its CID, which carries no position.
            apply_category(Categories.SHOP_DELI, item)
            yield item
