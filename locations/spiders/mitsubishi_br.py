from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MitsubishiBRSpider(StructuredDataSpider):
    name = "mitsubishi_br"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishimotors.com.br/concessionarias"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # The previous spider (pre-#17782) queried a dealer API that flagged each
        # location with newCars/postSalesServices/kitCarParts, letting us split
        # dealers into separate sales/service/parts items. That API is now
        # unreachable, and the AutoDealer entries in this page's structured data
        # (both the ld+json block and the embedded Next.js RSC payload) no longer
        # carry any equivalent per-function flags, so that split can't be
        # reconstructed from this source. All dealers are tagged as SHOP_CAR only.
        apply_category(Categories.SHOP_CAR, item)
        yield item
