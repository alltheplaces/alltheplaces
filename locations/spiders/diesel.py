from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DieselSpider(JSONBlobSpider):
    name = "diesel"
    item_attributes = {"brand": "Diesel", "brand_wikidata": "Q158285"}
    start_urls = [
        "https://uk.diesel.com/on/demandware.store/Sites-DieselCA-Site/en_CA/StoreFinder-SearchByBoundaries?latmin=-90&latmax=90&lngmin=-180&lngmax=180"
    ]
    locations_key = ["stores", "stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = item["ref"] = "https://uk.diesel.com/en/store-detail?sid={}".format(feature["ID"])
        item["branch"] = item.pop("name").removeprefix("Diesel Store ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
