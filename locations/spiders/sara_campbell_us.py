import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

PHONE_PATTERN = re.compile(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}")


class SaraCampbellUSSpider(Spider):
    name = "sara_campbell_us"
    item_attributes = {"brand": "Sara Campbell", "brand_wikidata": "Q117747597"}
    start_urls = ["https://saracampbell.com/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.css('div.map-section[data-section-type="section-map"]'):
            item = Feature()
            item["ref"] = item["branch"] = location.css("h2::text").get("").strip()
            item["addr_full"] = location.attrib.get("data-address")

            card_text = " ".join(t.strip() for t in location.css(".rte ::text").getall() if t.strip())
            if phone := PHONE_PATTERN.search(card_text):
                item["phone"] = phone.group()

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
