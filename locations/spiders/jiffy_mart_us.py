from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class JiffyMartUSSpider(UberallSpider):
    name = "jiffy_mart_us"
    item_attributes = {"brand": "Jiffy Mart", "brand_wikidata": "Q119592174"}
    key = "kcB7SIQENmVGSlzBQm6O3M8P6baM5K"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
