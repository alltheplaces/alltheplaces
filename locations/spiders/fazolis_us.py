from locations.categories import Categories, Extras, apply_yes_no
from locations.storefinders.yext_answers import YextAnswersSpider


class FazolisUSSpider(YextAnswersSpider):
    name = "fazolis_us"
    item_attributes = {"brand": "Fazoli's", "brand_wikidata": "Q1399195", "extras": Categories.FAST_FOOD.value}
    api_key = "e6cda871db03e0fc9eb2211470649126"
    experience_key = "locator"

    def parse_item(self, location, item):
        if amenities := location["data"].get("products"):
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-thru" in amenities, False)
            apply_yes_no(Extras.TAKEAWAY, item, "Take-out" in amenities, False)
            apply_yes_no(Extras.WIFI, item, "Free Wi-Fi" in amenities, False)
            apply_yes_no(Extras.WHEELCHAIR, item, "Handicap Accessible" in amenities, False)
        yield item
