from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AlaskaCommercialCompanyUSSpider(JSONBlobSpider):
    name = "alaska_commercial_company_us"
    item_attributes = {"brand": "Alaska Commercial Company", "brand_wikidata": "Q2637066"}
    start_urls = ["https://alaskacommercial.com/wp-admin/admin-ajax.php?action=get_ajax_zip_locations"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["name"] = self.item_attributes["brand"]
        item["phone"] = feature.get("phn")
        item["website"] = feature.get("store_link")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
