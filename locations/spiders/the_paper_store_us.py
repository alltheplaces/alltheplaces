from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class ThePaperStoreUSSpider(UberallSpider):
    name = "the_paper_store_us"
    item_attributes = {"brand": "The Paper Store", "brand_wikidata": "Q65068381"}
    key = "wdUDImqKHklW8zG0VfFBHTJ9JFZ4Nz"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item.pop("name", None)
        apply_category(Categories.SHOP_GIFT, item)
        yield item
