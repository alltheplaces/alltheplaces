from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.items import Feature


class KuoniGBSpider(JSONBlobSpider):
    name = "kuoni_gb"
    item_attributes = {"brand": "Kuoni", "brand_wikidata": "Q684355"}
    start_urls = ["https://www.kuoni.co.uk/api/appointment/get-stores/?r=20250609123615"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        item["branch"] = item.pop("name").removeprefix("Kuoni ")
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        yield item
