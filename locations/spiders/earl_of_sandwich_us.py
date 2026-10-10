import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The locations page lists every restaurant as a result card carrying its id,
# coordinates and page URL in data attributes. Address, phone and hours are only
# on each restaurant's page, as an address paragraph, a tel: link and a table of
# day and time rows.
#
# The list includes restaurants in Canada, France and the Philippines; their
# addresses carry no US state and postcode, and they are skipped.


class EarlOfSandwichUSSpider(Spider):
    name = "earl_of_sandwich_us"
    item_attributes = {"brand": "Earl of Sandwich", "brand_wikidata": "Q5326366"}
    allowed_domains = ["earlofsandwichusa.com"]
    start_urls = ["https://earlofsandwichusa.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for location in response.xpath('//li[contains(@class, "location")][@data-location-url]'):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["branch"] = location.xpath("@data-name").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["website"] = location.xpath("@data-location-url").get()

            yield response.follow(item["website"], callback=self.parse_location, cb_kwargs={"item": item})

    def parse_location(self, response: Response, item: Feature) -> Iterable[Feature]:
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in response.xpath(
                '//div[@id="address"]//h3[text()="Address"]/following-sibling::p[1]//text()'
            ).getall()
        ]
        lines = [line for line in lines if line]

        # "1553 S. Disneyland Drive" / "Anaheim, CA 92802", with the host venue
        # sometimes added on a line after the postcode.
        for index, line in enumerate(lines):
            if locality := re.fullmatch(r"(.+?),\s*([A-Z]{2})\s+(\d{5})", line):
                item["city"], item["state"], item["postcode"] = locality.groups()
                item["street_address"] = merge_address_lines(lines[:index])
                break
        else:
            return

        item["phone"] = response.xpath('//div[@id="phone"]//a[starts-with(@href, "tel:")]/text()').get()

        oh = OpeningHours()
        for row in response.xpath('//div[@id="hours"]//tr'):
            day = row.xpath("./th/text()").get("").strip()
            if day not in DAYS_3_LETTERS:
                continue
            times = row.xpath("./td/text()").get("").replace("\u2013", "-")
            if rule := re.fullmatch(r"\s*(\d{1,2}:\d{2}\s*[ap]m)\s*-\s*(\d{1,2}:\d{2}\s*[ap]m)\s*", times, re.I):
                oh.add_range(
                    day, rule.group(1).replace(" ", "").upper(), rule.group(2).replace(" ", "").upper(), "%I:%M%p"
                )
        item["opening_hours"] = oh if oh else None

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"

        yield item
