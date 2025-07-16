from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class LeeAUNZSpider(JSONBlobSpider):
    name = "lee_au_nz"
    item_attributes = {"brand": "Lee", "brand_wikidata": "Q1632681"}
    allowed_domains = ["leejeans.com.au"]
    start_urls = [
        "https://leejeans.com.au/on/demandware.store/Sites-au-leejeans-Site/en_AU/Stores-FindStores?storeType=lee%20outlet&radius=20000.0&lat=-23.12&long=132.13"
    ]
    locations_key = "stores"
    # HTTP 429 error received if the client looks like a bot. There appears to
    # be no other way to get store information except through this API.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
