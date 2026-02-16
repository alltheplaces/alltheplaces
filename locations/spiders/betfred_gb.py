from collections.abc import AsyncIterator, Iterable

import chompjs
from scrapy import FormRequest
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BetfredGBSpider(JSONBlobSpider):
    name = "betfred_gb"
    allowed_domains = ["www.betfredgroup.com"]
    item_attributes = {"brand": "Betfred", "brand_wikidata": "Q4897425"}
    seen = set()

    async def start(self) -> AsyncIterator[FormRequest]:
        for region in postal_regions("GB"):
            yield FormRequest(
                url="https://www.betfredgroup.com/shop-locator/",
                formdata={"submitted": "true", "location": region["postal_region"]},
            )

    def extract_json(self, response: TextResponse) -> list:
        if script := response.xpath('//script[contains(text(), "const json")]/text()').get():
            return chompjs.parse_js_object(script[script.index("const json") :])
        return []

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if item["ref"] in self.seen:
            return
        self.seen.add(item["ref"])
        item["branch"] = item.pop("name")
        oh = OpeningHours()
        oh.add_ranges_from_string(feature.get("OpeningHoursDescription", ""))
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_BOOKMAKER, item)
        yield item
