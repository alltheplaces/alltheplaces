from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DrKongHKSpider(JSONBlobSpider):
    name = "dr_kong_hk"
    item_attributes = {"brand": "Dr. Kong", "brand_wikidata": "Q116547631"}
    start_urls = ["https://webapi.91app.hk/webapi/LocationV2/GetLocationList?shopId=101&lang=en-HK"]
    locations_key = ["Data", "List"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = f"https://www.dr-kong.com.hk/Shop/StoreDetail/101/{item['ref']}"

        apply_category(Categories.SHOP_SHOES, item)

        yield item
