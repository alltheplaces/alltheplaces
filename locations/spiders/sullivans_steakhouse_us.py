from typing import Any, Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SullivansSteakhouseUSSpider(JSONBlobSpider):
    name = "sullivans_steakhouse_us"
    item_attributes = {"brand": "Sullivan's Steakhouse"}
    start_urls = ["https://www.sullivanssteakhouse.com/"]

    def extract_json(self, response: Response) -> list[dict]:
        script = response.xpath('//script[contains(text(), "ld_locations =")]/text()').get()
        return chompjs.parse_js_object(script[script.find("ld_locations =") + len("ld_locations =") :])

    def pre_process_data(self, location: dict) -> None:
        location.update(location.pop("address"))

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = location["post_title"]
        item["website"] = response.urljoin(location["post_name"] + "/")
        apply_category(Categories.RESTAURANT, item)
        yield item
