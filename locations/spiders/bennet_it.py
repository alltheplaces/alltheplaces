from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import FIREFOX_LATEST


class BennetITSpider(JSONBlobSpider):
    name = "bennet_it"
    item_attributes = {"brand": "Bennet", "brand_wikidata": "Q3638281"}
    start_urls = ["https://www.bennet.com/storefinder/nearestList?latitude=0&longitude=0&numberOfPos=1000"]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        feature.update(feature.pop("geoPoint"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["formattedAddress"]
        item.pop("street_address")
        item["branch"] = feature["displayName"]
        item["state"] = feature["province"]["provinceCode"]
        item["website"] = f"https://www.bennet.com/storefinder/iper/{feature['name']}"
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
