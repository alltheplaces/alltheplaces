import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The locations page lists each restaurant as a card holding the branch, the
# address across two lines, the phone and a link to the restaurant's page,
# where the hours are listed a day at a time.

ADDRESS = re.compile(r"(.+?),\s*([A-Za-z .]+)\s+(\d{5})")


class AllAmericanSteakhouseUSSpider(Spider):
    name = "all_american_steakhouse_us"
    item_attributes = {"brand": "The All American Steakhouse & Sports Theater"}
    allowed_domains = ["theallamericansteakhouse.com"]
    start_urls = ["https://theallamericansteakhouse.com/all-american-locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for card in response.xpath('//div[contains(@class, "locations-by-category__item")]'):
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in card.xpath('.//span[@class="address"]//text()').getall()
                if line.strip()
            ]
            # "3720 Churchville Rd" / "Aberdeen, Maryland 21001"
            if len(lines) < 2 or not (locality := ADDRESS.fullmatch(lines[-1])):
                continue

            item = Feature()
            # "Aberdeen, MD"
            item["branch"] = re.sub(
                r",\s*[A-Z]{2}$", "", re.sub(r"\s+", " ", card.xpath('.//h4[@class="title"]/text()').get("")).strip()
            )
            item["street_address"] = merge_address_lines(lines[:-1])
            item["city"], item["state"], item["postcode"] = locality.groups()
            item["phone"] = card.xpath('.//a[@class="phone"]/text()').get("").strip() or None
            item["website"] = card.xpath('.//a[@class="permalink"]/@href').get()
            item["ref"] = (item["website"] or "").rstrip("/").rsplit("/", 1)[-1]

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "steak_house"

            if item["website"]:
                yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})
            else:
                yield item

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        values = [
            re.sub(r"\s+", " ", value).replace("\u2013", "-").strip()
            for value in response.xpath('//*[contains(@class, "hours")]//text()').getall()
            if value.strip()
        ]

        oh = OpeningHours()
        for label, hours in zip(values, values[1:]):
            if not (day := DAYS_EN.get(label.title())):
                continue
            if times := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I):
                oh.add_range(
                    day,
                    times.group(1),
                    times.group(2),
                    time_format=["%I:%M%p", "%I:%M %p", "%I%p", "%I %p"],
                )
        if oh:
            item["opening_hours"] = oh

        yield item
