from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class CardzoneGBSpider(JSONBlobSpider):
    name = "cardzone_gb"
    item_attributes = {"brand": "Cardzone", "brand_wikidata": "Q123019897"}
    start_urls = [
        "https://cardzoneltd.com/wp-admin/admin-ajax.php?action=store_search&lat=52.95402&lng=-1.15499&max_results=300&search_radius=605&autoload=1"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["store"]
        item["street_address"] = clean_address([feature["address"],feature["address2"]])
        yield item
