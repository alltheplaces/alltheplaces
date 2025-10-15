from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.shahs_halal_food_us import ShahsHalalFoodUSSpider


class ShahsHalalFoodCASpider(JSONBlobSpider):
    name = "shahs_halal_food_ca"
    item_attributes = ShahsHalalFoodUSSpider.item_attributes
    allowed_domains = ["www.shahshalalfood.ca"]
    start_urls = ["https://www.shahshalalfood.ca/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        yield item
