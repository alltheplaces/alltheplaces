from html import unescape
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PedrosSpider(AgileStoreLocatorSpider):
    name = "pedros"
    item_attributes = {"brand": "Pedros", "brand_wikidata": "Q124382243"}
    allowed_domains = ["pedroschicken.co.za"]
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = unescape(item.pop("street_address"))
        item["branch"] = item.pop("name").removeprefix("Pedros ")
        yield item
