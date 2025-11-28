from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NetworkTRSpider(JSONBlobSpider):
    name = "network_tr"
    item_attributes = {"brand": "Network", "brand_wikidata": "Q28736409"}
    start_urls = ["https://www.network.com.tr/Lookup/OfflineStores"]
    locations_key = "Result"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["MAGAZATITLE"]
        item["branch"] = feature["MAGAZATITLE"].replace(" NetWork", "")
        item["addr_full"] = feature["ADRES"]
        item["city"] = feature["IL"]
        item["phone"] = feature["MAGAZATEL"]
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
