from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext import YextSpider


class FazolisUSSpider(YextSpider):
    name = "fazolis_us"
    item_attributes = {"brand": "Fazoli's", "brand_wikidata": "Q1399195"}
    api_key = "e6cda871db03e0fc9eb2211470649126"

    def parse_item(self, item, location):
        if location.get("c_pagesURL"):
            item["website"] = location["c_pagesURL"]
        item.pop("twitter")
        item["extras"].pop("contact:instagram", None)
        if location.get("products"):
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-thru" in location["products"], False)
            apply_yes_no(Extras.TAKEAWAY, item, "Take-out" in location["products"], False)
            apply_yes_no(Extras.WIFI, item, "Free Wi-Fi" in location["products"], False)
            apply_yes_no(Extras.WHEELCHAIR, item, "Handicap Accessible" in location["products"], False)
        yield item
