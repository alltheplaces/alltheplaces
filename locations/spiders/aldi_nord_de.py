from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


# Does have Linked Data, but requires JS to load it
class AldiNordDESpider(UberallSpider):
    name = "aldi_nord_de"
    item_attributes = {"brand": "Aldi Nord", "brand_wikidata": "Q41171373"}
    drop_attributes = {"name"}
    key = "ALDINORDDE_UimhY3MWJaxhjK9QdZo3Qa4chq1MAu"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
