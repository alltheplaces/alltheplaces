from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class DuneLondonSpider(JSONBlobSpider):
    name = "dune_london"
    item_attributes = {"brand": "Dune London", "brand_wikidata": "Q65557112"}
    start_urls = [
        "https://www.dunelondon.com/on/demandware.store/Sites-DuneUK-Site/en_GB/Stores-FindStores?showMap=false&radius=12000&lat=30.5072178&long=-1.1275862&src=store",
    ]
    locations_key = ["stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Dune ").removeprefix("DUNE ")
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        apply_category(Categories.SHOP_SHOES, item)
        yield item
