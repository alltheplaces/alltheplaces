import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

STATE_CODES = {
    "colorado": "CO",
    "florida": "FL",
    "georgia": "GA",
    "kentucky": "KY",
    "michigan": "MI",
    "north-carolina": "NC",
    "ohio": "OH",
    "pennsylvania": "PA",
    "tennessee": "TN",
    "texas": "TX",
    "virginia": "VA",
    "west-virginia": "WV",
}


class PeaceLoveAndLittleDonutsUSSpider(Spider):
    name = "peace_love_and_little_donuts_us"
    item_attributes = {"brand": "Peace, Love & Little Donuts"}
    allowed_domains = ["www.peaceloveandlittledonuts.com"]
    start_urls = ["https://www.peaceloveandlittledonuts.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in response.xpath(
            '//div[contains(@class, "state-collection-wrapper")]//a[starts-with(@href, "/states/")]/@href'
        ).getall():
            yield response.follow(url, callback=self.parse_state)

    def parse_state(self, response: Response) -> Iterable[Request]:
        state = STATE_CODES[response.url.rstrip("/").rsplit("/", 1)[-1]]
        for url in response.xpath(
            '//div[contains(@class, "store-location-wrapper")]//a[starts-with(@href, "/locations/")]/@href'
        ).getall():
            yield response.follow(url, callback=self.parse_location, cb_kwargs={"state": state})

    def parse_location(self, response: Response, state: str) -> Iterable[Feature]:
        if response.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " coming-soon ") '
            'and not(contains(@class, "w-condition-invisible"))]'
        ):
            return

        address = response.xpath(
            '//div[normalize-space()="Address"]/following-sibling::a[contains(@class, "location")][1]/text()'
        ).get()

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = response.xpath('//div[contains(@class, "chalkboard-title")]/text()').get()
        item["addr_full"] = address
        item["state"] = state
        if postcodes := re.findall(r"\b\d{5}(?:-\d{4})?\b", address or ""):
            item["postcode"] = postcodes[-1]
        item["country"] = "US"
        item["phone"] = response.xpath('//div[normalize-space()="Phone"]/following-sibling::a[1]/@href').get()
        item["website"] = response.url
        item["facebook"] = response.xpath('//a[contains(@class, "follow-us-button")]/@href').get()

        apply_category(Categories.SHOP_BAKERY, item)
        item["extras"]["cuisine"] = "donut"
        yield item
