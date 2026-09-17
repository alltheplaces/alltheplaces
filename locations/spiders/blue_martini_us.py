import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature

# Every lounge has its own subdomain, linked from the brand site's navigation,
# and publishes its address, phone and hours on a /contact/ page as an icon
# prefixed list.
#
# The map links are goo.gl short links, so no coordinates are available without
# resolving each one.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BlueMartiniUSSpider(Spider):
    name = "blue_martini_us"
    item_attributes = {"brand": "Blue Martini"}
    allowed_domains = ["bluemartini.com"]
    start_urls = ["https://bluemartini.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        subdomains = set(
            re.findall(r"https://([a-z]+)\.bluemartini\.com", " ".join(response.xpath("//a/@href").getall()))
        )
        for subdomain in sorted(subdomains):
            yield response.follow(f"https://{subdomain}.bluemartini.com/contact/", callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        details = response.xpath('//ul[contains(@class, "fa-ul")][.//i[contains(@class, "fa-location-dot")]]')
        if not details:
            return

        address = details.xpath('.//i[contains(@class, "fa-location-dot")]/ancestor::li//a/text()').get()
        # "2432 E Sunrise Blvd, Fort Lauderdale, FL 33304"
        if not (parts := re.fullmatch(r"(.+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})", (address or "").strip())):
            return

        item = Feature()
        item["ref"] = response.url.split("//", 1)[1].split(".", 1)[0]
        item["branch"] = details.xpath("preceding-sibling::h3[1]/text()").get()
        item["website"] = response.url
        item["street_address"], item["city"], item["state"], item["postcode"] = [
            part.strip() for part in parts.groups()
        ]
        # The first number is the main line; later ones reach managers.
        item["phone"] = details.xpath('.//a[starts-with(@href, "tel:")]/text()').get()

        item["opening_hours"] = self.parse_opening_hours(details)

        apply_category(Categories.BAR, item)

        yield item

    @staticmethod
    def parse_opening_hours(details: Selector) -> OpeningHours | None:
        """Parses a list of "Su: 4PM-2AM" lines."""
        oh = OpeningHours()

        for line in details.xpath('.//i[contains(@class, "fa-clock")]/ancestor::li//text()').getall():
            if not (
                rule := re.match(
                    r"\s*([A-Za-z]{2,9})\s*:\s*(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)",
                    line,
                    re.I,
                )
            ):
                continue
            if not (day := sanitise_day(rule.group(1))):
                continue

            oh.add_range(
                day,
                BlueMartiniUSSpider.normalise_time(rule.group(2)),
                BlueMartiniUSSpider.normalise_time(rule.group(3)),
                time_format="%I:%M%p",
            )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").lower()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
