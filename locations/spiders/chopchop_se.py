import re
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class ChopchopSESpider(Spider):
    name = "chopchop_se"
    item_attributes = {
        "brand": "ChopChop Asian Express",
        "brand_wikidata": "Q104631081",
        "country": "SE",
    }
    allowed_domains = ["chopchop.se"]
    start_urls = ["https://chopchop.se/bestallonline/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//div[contains(@class, "e-loop-item") and contains(@class, "restaurant")]'):
            item = Feature()

            name = store.xpath('.//h3[contains(@class, "elementor-heading-title")]/text()').get()
            if name:
                item["name"] = name.strip()

            link = store.xpath('.//a[contains(@href, "chopchop.se/restaurant/")]/@href').get()
            if link:
                item["website"] = link
                item["ref"] = link.rstrip("/").split("/")[-1]

            addr_full = store.xpath('.//div[contains(@class, "hitta-card-location")]/text()').get()
            if addr_full:
                item["addr_full"] = addr_full.strip()

            text_editors = store.xpath(
                './/div[contains(@class, "elementor-widget-text-editor") and not(contains(@class, "hitta-card-location"))]/text()'
            ).getall()
            if len(text_editors) >= 1:
                item["street_address"] = text_editors[0].strip()
            hours_str = text_editors[1].strip() if len(text_editors) >= 2 else None
            if hours_str:
                hours_str = hours_str.replace("\u2013", "-").replace(".", ":")
                if m := re.match(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", hours_str):
                    oh = OpeningHours()
                    oh.add_ranges_from_string(f"Mo-Su {m.group(1)}-{m.group(2)}")
                    item["opening_hours"] = oh

            apply_category(Categories.FAST_FOOD, item)

            if link:
                yield Request(url=link, callback=self.parse_store, meta={"item": item})
            else:
                yield item

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = response.meta["item"]
        extract_google_position(item, response)
        yield item
