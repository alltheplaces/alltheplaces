from typing import Any, Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SweetfrogUSSpider(JSONBlobSpider):
    name = "sweetfrog_us"
    item_attributes = {"brand": "sweetFrog", "brand_wikidata": "Q16952110"}
    start_urls = ["https://locator.kahalamgmt.com/locator/index.php?mode=desktop&brand=38"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def extract_json(self, response: Response) -> list[dict]:
        return [
            parse_js_object(line.split(" = ", 1)[1])
            for line in response.text.splitlines()
            if "Locator.stores[" in line and " = {" in line
        ]

    def pre_process_data(self, location: dict) -> None:
        location["street_address"] = location.pop("Address")

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        item["website"] = "https://www.sweetfrog.com/stores/frozen-yogurt-{}/{}".format(
            location["cleanCity"], location["StoreId"]
        )
        apply_category(Categories.ICE_CREAM, item)
        yield item
