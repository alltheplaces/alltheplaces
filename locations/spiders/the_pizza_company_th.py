from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ThePizzaCompanyTHSpider(JSONBlobSpider):
    name = "the_pizza_company_th"
    item_attributes = {"brand": "The Pizza Company", "brand_wikidata": "Q2413520"}
    start_urls = ["https://api2.1112.com/api/v1/store-service?store_type=RBD,DLC,DWS,FSR"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Pizza Com ")
        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
