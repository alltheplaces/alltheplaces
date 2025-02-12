from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NatuzziSpider(JSONBlobSpider):
    name = "natuzzi"
    item_attributes = {"brand": "Natuzzi", "brand_wikidata": "Q3873359"}
    start_urls = ["https://api.natuzzi.com/api/storelocator/italia/all"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        if feature["type"] in [
            "EDOS",  # Office
            "GALLERY",  # "Natuzzi Italia Gallery" / shop in a shop
            "POINT",
        ]:
            return

        item["name"] = None
        item["branch"] = feature["shortName"]
        item["website"] = urljoin("https://www.natuzzi.com/gb/en/stores/", feature["slug"])
        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
