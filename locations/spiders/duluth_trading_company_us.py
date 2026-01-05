from json import loads
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class DuluthTradingCompanyUSSpider(JSONBlobSpider):
    name = "duluth_trading_company_us"
    item_attributes = {"brand": "Duluth Trading Company", "brand_wikidata": "Q48977107"}
    allowed_domains = ["www.duluthtrading.com"]
    start_urls = ["https://www.duluthtrading.com/mobify/proxy/ocapi/s/DTC/api/store/all/"]
    needs_json_request = True
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("store"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("storeStatus") != "open":
            # Store that is coming soon (not yet open).
            return
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        item["website"] = "https://www.duluthtrading.com/locations/?StoreID=" + item["ref"]

        item["opening_hours"] = OpeningHours()
        hours = loads(feature.get("hours"))
        for day_name in DAYS_FULL:
            if day_hours := hours.get(day_name):
                item["opening_hours"].add_range(day_name, day_hours["open"], day_hours["close"])

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
