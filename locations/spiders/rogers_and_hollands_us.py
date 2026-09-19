import html
import json
import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The store finder page carries every store in the map's data-locations
# attribute, with the address and phone inside a chunk of HTML per store.
# Opening hours are only on the store pages, as a list of "Monday: 10:00AM -
# 8:00PM" items.
#
# The company trades under two names, so the brand is taken from each store's
# own name rather than being set for the whole spider.

BRANDS = {
    "Rogers & Hollands Jewelers": "Q130223859",
    "Ashcroft & Oak Jewelers": None,
}


class RogersAndHollandsUSSpider(Spider):
    name = "rogers_and_hollands_us"
    allowed_domains = ["www.rogersandhollands.com", "rogersandhollands.com"]
    start_urls = ["https://www.rogersandhollands.com/find-a-store"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        if not (locations := response.xpath("//*[@data-locations]/@data-locations").get()):
            self.logger.error("No locations on the store finder page")
            return

        for location in json.loads(locations):
            details = Selector(text=html.unescape(location["infoWindowHtml"]))

            item = Feature()
            item["ref"] = details.xpath("//div[@data-store-id]/@data-store-id").get()
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            item["branch"] = details.xpath('//h2[contains(@class, "store-zip")]/text()').get()
            item["phone"] = details.xpath('//a[contains(@class, "storelocator-phone")]/text()').get()
            item["website"] = details.xpath('//a[contains(@class, "store-link")]/@href').get()

            if brand := location.get("name"):
                item["brand"] = brand
                item["brand_wikidata"] = BRANDS.get(brand)

            self.parse_address(item, details)

            apply_category(Categories.SHOP_JEWELRY, item)

            if item["website"]:
                yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})
            else:
                yield item

    @staticmethod
    def parse_address(item: Feature, details: Selector) -> None:
        """The address is a run of paragraphs, the last holding city, state and postcode."""
        lines = [re.sub(r"\s+", " ", line).strip(" ,") for line in details.xpath("//address/p//text()").getall()]
        lines = [line for line in lines if line]

        for index, line in enumerate(lines):
            if locality := re.fullmatch(r"(.+?),?\s*([A-Z]{2}),?\s*(\d{5})", line):
                item["city"], item["state"], item["postcode"] = [part.strip() for part in locality.groups()]
                item["street_address"] = merge_address_lines(lines[:index])
                return

        item["addr_full"] = merge_address_lines(lines)

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        oh = OpeningHours()

        for line in response.xpath('//h5[contains(text(), "Store Hours")]/following-sibling::ul[1]/li/text()').getall():
            if not (
                rule := re.fullmatch(
                    r"\s*(\w+):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)\s*", line, re.I
                )
            ):
                continue
            if day := DAYS_EN.get(rule.group(1).title()):
                oh.add_range(
                    day, rule.group(2).replace(" ", "").upper(), rule.group(3).replace(" ", "").upper(), "%I:%M%p"
                )

        if oh.as_opening_hours():
            item["opening_hours"] = oh

        yield item
