from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class OrchestraFRSpider(UberallSpider):
    name = "orchestra_fr"
    item_attributes = {"brand": "Orchestra", "brand_wikidata": "Q28042940"}
    key = "fRYpR2RHA3bSUaYQIhuOkMIvP9eIVf"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").title().removeprefix("Orchestra ")

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
