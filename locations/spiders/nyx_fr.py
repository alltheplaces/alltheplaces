from typing import Iterable

from pyproj import Geod
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class NyxFRSpider(JSONBlobSpider):
    name = "nyx_fr"
    start_urls = [
        "https://www.nyxcosmetics.fr/on/demandware.store/"
        "Sites-nyx-fr-v2-Site/fr_FR/Stores-Search"
        "?lat=46.27&long=1.70&searchDistance=1000&ajax=true"
    ]
    item_attributes = {"brand": "Nyx", "brand_wikidata": "Q23671513"}
    locations_key = ["storelocatorresults", "stores"]
    needs_json_request = True
    name_is_branch = True
    geod_obj = Geod(ellps="WGS84")
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item["branch"].removeprefix("NYX Professional Makeup ")
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
