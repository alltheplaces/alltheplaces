from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class TheEntertainerGBSpider(JSONBlobSpider):
    name = "the_entertainer_gb"
    item_attributes = {"brand": "The Entertainer", "brand_wikidata": "Q7732289"}
    start_urls = [
        "https://www.thetoyshop.com/api/occ/v2/thetoyshop/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=1200&query=doncaster&storeType=ALL&radius=10000000&sort=asc"
    ]
    locations_key = ["stores"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # No robots.txt
        "DEFAULT_REQUEST_HEADERS": {
            "Content-Type": "application/json",
            "Host": "www.thetoyshop.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.thetoyshop.com/store-finder?",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
        },
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["address"]["id"]
        item["website"] = "https://www.thetoyshop.com" + item["website"]
        item["street_address"] = merge_address_lines([feature["address"].get("line1"), feature["address"].get("line2")])
        item["branch"] = item.pop("name")
        yield item
