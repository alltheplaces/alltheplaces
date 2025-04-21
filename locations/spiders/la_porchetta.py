from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LaPorchettaSpider(WPStoreLocatorSpider):
    name = "la_porchetta"
    item_attributes = {"brand": "La Porchetta", "brand_wikidata": "Q6464528"}
    start_urls = ["https://laporchetta.com.au/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
