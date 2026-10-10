import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class DevredSpider(Spider):
    name = "devred"
    item_attributes = {"brand": "Devred", "brand_wikidata": "Q3025542"}
    start_urls = ["https://devred.com/pages/nos-boutiques"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.css("div.store-locator__store"):
            item = Feature()
            item["ref"] = store.attrib["data-store-id"]
            item["branch"] = store.attrib["data-store-name"].removeprefix("Devred 1902 ")
            item["lat"] = store.attrib["data-store-lat"]
            item["lon"] = store.attrib["data-store-lng"]
            item["street_address"] = store.attrib["data-store-address"]
            item["city"] = store.attrib["data-store-city"]
            item["postcode"] = store.attrib["data-store-postal"]
            item["phone"] = store.attrib.get("data-store-phone")
            item["website"] = response.urljoin(store.attrib["data-store-url"])
            item["opening_hours"] = YextAnswersSpider.parse_opening_hours(json.loads(store.attrib["data-store-hours"]))
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
