from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS
from locations.user_agents import BROWSER_DEFAULT

TOYOTA_SHARED_ATTRIBUTES = {"brand": "Toyota", "brand_wikidata": "Q53268"}


class ToyotaAUSpider(JSONBlobSpider, PlaywrightSpider):
    name = "toyota_au"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    allowed_domains = ["www.toyota.com.au"]
    start_urls = [
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/ACT?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/NSW?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/NT?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/QLD?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/SA?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/TAS?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/VIC?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/WA?dealerOptIn=false",
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS | {"USER_AGENT": BROWSER_DEFAULT}
    locations_key = "results"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature["refY"]
        item["lon"] = feature["refX"]
        item["state"] = feature["state"]
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = feature["webSite"]

        if feature.get("sales"):
            sales = item.deepcopy()
            sales["ref"] = feature["branchCode"] + "_sales"
            apply_category(Categories.SHOP_CAR, sales)
            yield sales
        if feature.get("service"):
            service = item.deepcopy()
            service["ref"] = feature["branchCode"] + "_service"
            apply_category(Categories.SHOP_CAR_REPAIR, service)
            yield service
        if feature.get("parts"):
            parts = item.deepcopy()
            parts["ref"] = feature["branchCode"] + "_parts"
            apply_category(Categories.SHOP_CAR_PARTS, parts)
            yield parts
