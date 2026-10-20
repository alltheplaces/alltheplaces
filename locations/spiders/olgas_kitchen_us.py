from typing import Any, Iterable

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class OlgasKitchenUSSpider(Spider):
    name = "olgas_kitchen_us"
    item_attributes = {"brand": "Olga's Kitchen"}
    allowed_domains = ["www.olgas.com"]
    start_urls = ["https://www.olgas.com/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["slug"]
            item["branch"] = location["name"]
            item["name"] = None
            item.pop("addr_full", None)
            item["street"] = None
            item["street_address"] = location.get("street")
            item["phone"] = location.get("phone_number")
            item["website"] = response.urljoin(location["url"])

            hours_text = " ".join(
                text.strip()
                for text in Selector(text=location.get("hours") or "").xpath("//text()").getall()
                if text.strip() and "order " not in text.lower()
            )
            hours = OpeningHours()
            hours.add_ranges_from_string(hours_text, days=DAYS_EN)
            item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "greek"
            yield item
