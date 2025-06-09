from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class RegisGBSpider(UberallSpider):
    name = "regis_gb"
    item_attributes = {"brand": "Regis Salons", "brand_wikidata": "Q110166032"}
    key = "616eo7rrGeXiZ0jL1wrJ2JAlyx5RxR"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Regis Salon ")
        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item
