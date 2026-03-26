from typing import Any, AsyncIterator, Iterable

from scrapy.http import Request, Response
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT

class LOccitaneGBSpider(JSONBlobSpider):
    name = "l_occitane_gb"
    item_attributes = {"brand": "L'Occitane", "brand_wikidata": "Q1880676"}
    start_urls = ["https://uk.loccitane.com/on/demandware.store/Sites-OCC_GB-Site/en_GB/Stores-GetStores?countryCode=GB"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",

        }
    }
    locations_key = ["stores"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item
