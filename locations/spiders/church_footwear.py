import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class ChurchFootwearSpider(JSONBlobSpider):
    name = "church_footwear"
    item_attributes = {"brand": "Church's", "brand_wikidata": "Q2967663"}
    start_urls = ["https://api.church-footwear.com/anon/mwstorestore/store/v2?langId=en_GB"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "api.church-footwear.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.church-footwear.com/",
            "storeId": "churchsStore-GB",
            "Origin": "https://www.church-footwear.com",
        },
    }
    locations_key = "allStores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "SC" in item["name"]:
            branch = feature["Description"]["displayStoreName"]
            lowername = re.sub("[^0-9a-zA-Z]+", "-", branch.lower())
            item["branch"] = branch.replace("Church's ", "")
            item["website"] = (
                "https://www.church-footwear.com/gb/en/store-locator/" + lowername + "/" + item["name"] + ".html"
            )
            item.pop("name", None)
            yield item
