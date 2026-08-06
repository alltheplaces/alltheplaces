from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class ToyotaMXSpider(JSONBlobSpider):
    name = "toyota_mx"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = ["https://www.toyota.mx/graphql/execute.json/tmex/distributorByStates"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def extract_json(self, response: Response) -> list[dict]:
        return [
            dict(store, state=data["state"])
            for data in response.json()["data"]["stateDistributorsList"]["items"]
            for store in data["distributors"]
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = str(feature["dealerCode"])
        item["addr_full"] = feature["address"]["plaintext"]
        item["state"] = feature["state"]
        apply_category(Categories.SHOP_CAR, item)
        yield item
