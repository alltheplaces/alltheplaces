import re

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.mitsubishi import MitsubishiSpider


class MitsubishiBELUSpider(JSONBlobSpider):
    name = "mitsubishi_be_lu"
    item_attributes = MitsubishiSpider.item_attributes
    start_urls = ["https://mitsubishi-motors.be/dealers.json"]
    locations_key = "dealers"
    skip_auto_cc_spider_name = True

    def pre_process_data(self, feature: dict):
        for key in list(feature.keys()):
            if key.startswith("Dealer"):
                feature[key.removeprefix("Dealer")] = feature.pop(key)

    def post_process_item(self, item: Feature, response: Response, location: dict):
        item["ref"] = location["Number"]
        item["addr_full"] = clean_address(
            [
                location.get("Address_1", ""),
                location.get("Address_2", ""),
                location.get("Address_3", ""),
                location.get("Address_4", ""),
                location.get("Address_5", ""),
                location.get("PostCode", ""),
            ]
        )
        item["website"] = location.get("WebSite")
        item["email"] = location.get("PrincipalEmail")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            for start_time, end_time in re.findall(
                r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", location.get("Service{}Open".format(day)) or ""
            ):
                item["opening_hours"].add_range(day, start_time, end_time)

        if location.get("Status", "").lower() == "service only":
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            self.logger.error(f'Unknown type: {location.get("Status")}, {item["name"]}, {item["ref"]}')

        yield item
