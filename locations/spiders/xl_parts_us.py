import html
import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class XlPartsUSSpider(Spider):
    name = "xl_parts_us"
    item_attributes = {"brand": "XL Parts", "brand_wikidata": "Q123188576"}
    start_urls = ["https://www.xlparts.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.xpath('//div[contains(@class, "store-list-item")]'):
            if store.xpath("./@data-brand").get() != "XL Parts":
                continue

            item = Feature()
            title = store.xpath("./@data-title").get("")
            if m := re.match(r"^(\d+)\s*-\s*(.+)$", title):
                item["ref"], item["branch"] = m.group(1), m.group(2).strip()
            else:
                item["ref"] = title.strip()
            item["street_address"] = store.xpath("./@data-address").get()
            item["city"] = store.xpath("./@data-city").get()
            item["state"] = store.xpath("./@data-state").get()
            item["postcode"] = (store.xpath("./@data-zip").get() or "").strip()
            item["lat"] = store.xpath("./@data-lat").get()
            item["lon"] = store.xpath("./@data-lng").get()
            item["phone"] = store.xpath("./@data-phone").get()

            oh = OpeningHours()
            if hours_attr := store.xpath("./@data-hours").get():
                for entry in json.loads(html.unescape(hours_attr)):
                    if entry.get("closed"):
                        continue
                    oh.add_range(DAYS[entry["day"] - 1], entry["open"], entry["close"], time_format="%H:%M:%S")
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_CAR_PARTS, item)
            yield item
