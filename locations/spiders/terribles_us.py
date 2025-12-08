from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TerriblesUSSpider(AgileStoreLocatorSpider):
    name = "terribles_us"
    item_attributes = {
        "name": "Terrible's",
        "brand": "Terrible's",
        "brand_wikidata": "Q7703648",
        "extras": Categories.CAR_WASH.value,
    }
    allowed_domains = ["www.terribles.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = item.pop("name").removeprefix("Terrible's Car Wash ")
        yield item
