from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiFRSpider(JSONBlobSpider):
    name = "mitsubishi_fr"
    start_urls = ["https://www.mitsubishi-motors.fr/wp-admin/admin-ajax.php?action=store_search&make=-1&autoload=1"]
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["store"]
        item["street_address"] = item.pop("addr_full")
        for dept in feature["store_type"].split(" et/ou "):
            if dept == "Ventes":
                sales_item = item.deepcopy()
                sales_item["ref"] = str(sales_item["ref"]) + "-SALES"
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item
            elif dept == "Après-vente":
                service_item = item.deepcopy()
                service_item["ref"] = str(service_item["ref"]) + "-SERVICE"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
