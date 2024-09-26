from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_EN
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiCASpider(JSONBlobSpider):
    name = "hyundai_ca"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["apps.hac.ca"]
    start_urls = ["https://apps.hac.ca/api/getdealers?numberdealers=1000&languagecode=en&latitude=43.653226&longitude=-79.3831843"]
    locations_key = ["DealerList", "Dealers", "Dealer"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item.get("website") and item["website"].startswith("www."):
            item["website"] = "https://" + item["website"]
        if feature.get("Hours"):
            if "Sales" in feature["Hours"].keys():
                item["ref"] = feature.get("DealerCode") + "_Sales"
                sales = item.copy()
                apply_category(Categories.SHOP_CAR, sales)
                sales["opening_hours"] = self.parse_opening_hours(feature, "Sales")
                yield sales
            if "Service" in feature["Hours"].keys():
                item["ref"] = feature.get("DealerCode") + "_Service"
                service = item.copy()
                apply_category(Categories.SHOP_CAR_REPAIR, service)
                service["opening_hours"] = self.parse_opening_hours(feature, "Service")
                yield service
            if "Parts" in feature["Hours"].keys():
                item["ref"] = feature.get("DealerCode") + "_Parts"
                parts = item.copy()
                apply_category(Categories.SHOP_CAR_PARTS, parts)
                parts["opening_hours"] = self.parse_opening_hours(feature, "Parts")
                yield parts

    def parse_opening_hours(self, feature: dict, hours_type: str) -> OpeningHours():
        oh = OpeningHours()
        if not feature.get("Hours"):
            return oh
        if hours_type not in feature["Hours"]:
            return oh
        for day_hours in feature["Hours"][hours_type]["Days"]:
            if day_hours["Start"] == "--" or day_hours["Start"] == "By Appt. Only" or day_hours["End"] == "--" or day_hours["End"] == "By Appt. Only":
                oh.set_closed(DAYS_EN[day_hours["Weekday"]])
            else:
                oh.add_range(DAYS_EN[day_hours["Weekday"]], day_hours["Start"], day_hours["End"], "%I:%M %p")
        return oh
