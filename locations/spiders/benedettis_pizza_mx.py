from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BenedettisPizzaMXSpider(JSONBlobSpider):
    name = "benedettis_pizza_mx"
    item_attributes = {"brand": "Benedetti's Pizza", "brand_wikidata": "Q4887212"}
    start_urls = ["https://www.benedettis.com/locales"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = chompjs.parse_js_object(response.xpath('//*[contains(text(),"stores")]/text()').get())["state"][
            "loaderData"
        ]["pages/WebsiteDynamicPages/route"]["activeComponents"][0]["data"]["stores"]
        return json_data

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        feature.update(feature.pop("supportOptions"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["_id"]
        item["branch"] = item.pop("name")
        item.pop("email")
        apply_category(Categories.FAST_FOOD, item)
        yield item
