from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.structured_data_spider import clean_facebook, clean_instagram


class GiantAUSpider(JSONBlobSpider):
    name = "giant_au"
    item_attributes = {"brand": "Giant", "brand_wikidata": "Q703557"}
    allowed_domains = ["www.giant-bicycles.com"]
    start_urls = ["https://www.giant-bicycles.com/au/stores/dealers"]
    locations_key = "dealers"

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {
            "campaigncodes": [],
            "keyword": "",
            "latitude": -37.8152065,
            "longitude": 144.963937,
            "NE_lat": 0,
            "NE_lng": 0,
            "onlyGiantStores": True,
            "SW_lat": 0,
            "SW_lng": 0,
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Code"]
        item["branch"] = item.pop("name", None).removeprefix("Giant ")
        item["addr_full"] = feature["AddressLocalized"]
        if item["website"] and not item["website"].startswith("http"):
            item["website"] = "https://{}".format(item["website"])
        if feature["Facebook"]:
            item["facebook"] = clean_facebook(feature["Facebook"])
        if feature["Instagram"]:
            item["instagram"] = clean_instagram(feature["Instagram"])
        if feature["Image"]:
            item["image"] = feature["Image"]
        apply_category(Categories.SHOP_BICYCLE, item)
        yield item
