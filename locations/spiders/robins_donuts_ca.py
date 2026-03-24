from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class RobinsDonutsCASpider(UberallSpider):
    name = "robins_donuts_ca"
    item_attributes = {"brand": "Robin's Donuts", "brand_wikidata": "Q7352199"}
    key = "VKUHLIZZDXHUKKWJ"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
