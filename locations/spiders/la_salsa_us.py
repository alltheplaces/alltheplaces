from typing import Any, Iterable

import chompjs
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LaSalsaUSSpider(JSONBlobSpider):
    name = "la_salsa_us"
    item_attributes = {"brand": "La Salsa", "brand_wikidata": "Q48835190"}
    start_urls = ["https://www.lasalsa.com/locator/index.php?brand=26&mode=desktop&pagesize=7000&q=us"]

    def extract_json(self, response: Response) -> Iterable[dict]:
        for location_js in response.xpath("//div[starts-with(@id, 'store_')]/script/text()").getall():
            yield chompjs.parse_js_object(location_js.split(" = ", 1)[1])

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Any:
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        item["website"] = response.urljoin(f"/stores/{location['SEOPath']}/{location['StoreId']}")
        apply_category(Categories.FAST_FOOD, item)
        yield Request(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        oh = OpeningHours()
        for line in response.xpath('//div[@class="dineInHours"]//li/text()').getall():
            oh.add_ranges_from_string(line)
        item["opening_hours"] = oh
        yield item
