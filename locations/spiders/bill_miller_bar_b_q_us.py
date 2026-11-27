from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class BillMillerBarBQUSSpider(Spider):
    name = "bill_miller_bar_b_q_us"
    item_attributes = {"brand": "Bill Miller Bar-B-Q", "brand_wikidata": "Q4910194"}
    allowed_domains = ["www.billmillerbbq.com"]
    start_urls = ["https://www.billmillerbbq.com/all-locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in set(response.css("a::attr(href)").re(r".*/locations/bill-miller-[a-z0-9-]+/$")):
            yield response.follow(url, callback=self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        location = chompjs.parse_js_object(response.text.split('"locations":', 1)[1].split("};", 1)[0])[0]

        item = DictParser.parse(location)
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = location["store"].removeprefix("Bill Miller ")
        item["name"] = None
        item["phone"] = response.css('a[href^="tel:"]::attr(href)').get()
        item["website"] = response.url

        oh = OpeningHours()
        for row in response.css("span.day-of-week"):
            day = row.css("::text").get().strip().removesuffix(":")[:2].title()
            hours = row.xpath('following-sibling::span[contains(@class, "hours")]/text()').get()
            if hours:
                oh.add_ranges_from_string(f"{day} {hours}")
        item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)

        yield item
