from typing import Any, Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TacoTimeUSSpider(JSONBlobSpider):
    name = "taco_time_us"
    item_attributes = {"brand": "Taco Time", "brand_wikidata": "Q7673969"}
    start_urls = ["https://www.tacotime.com/stores/"]

    def extract_json(self, response: Response) -> list[dict]:
        return [
            parse_js_object(line.split(" = ", 1)[1])
            for line in response.text.splitlines()
            if "Locator.stores[" in line and " = {" in line
        ]

    def pre_process_data(self, location: dict) -> None:
        location["street_address"] = location.pop("Address")

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = response.urljoin(f"/stores/{location['StoreId']}")
        apply_category(Categories.FAST_FOOD, item)
        yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            "; ".join(response.xpath('//div[@class="dineInHours"]//li/text()').getall())
        )
        yield item
