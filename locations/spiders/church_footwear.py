import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChurchFootwearSpider(JSONBlobSpider):
    name = "church_footwear"
    item_attributes = {"brand": "Church's", "brand_wikidata": "Q2967663"}
    start_urls = ["https://api.church-footwear.com/anon/mwstorestore/store/v2?langId=en_GB"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"storeId": "churchsStore-GB"}}
    locations_key = "allStores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "SC" in item["name"]:
            branch = feature["Description"]["displayStoreName"]
            lowername = re.sub("[^0-9a-zA-Z]+", "-", branch.lower())
            item["branch"] = branch.removeprefix("Church's ").removeprefix("Church’s ")
            if item["branch"] == "Factory Shop":
                item["branch"] = None
                item["name"] = "Church's Factory Shop"
            else:
                item["name"] = None
            item["website"] = (
                "https://www.church-footwear.com/gb/en/store-locator/" + lowername + "/" + item["ref"] + ".html"
            )

            apply_category(Categories.SHOP_SHOES, item)

            yield item
