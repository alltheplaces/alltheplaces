from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.storefinders.yext import YextSpider


class TropicalSmoothieCafeUSSpider(YextSpider):
    name = "tropical_smoothie_cafe_us"
    item_attributes = {"brand": "Tropical Smoothie Cafe", "brand_wikidata": "Q7845817"}
    api_key = "e00ed8254f827f6c73044941473bb9e9"

    def parse_item(self, item, location):
        item["email"] = location.get("c_cafeEmail")
        apply_yes_no(Extras.DRIVE_THROUGH, item, "DRIVE_THRU" in location.get("c_locationPageServices", []), False)
        apply_yes_no(Extras.DELIVERY, item, "DELIVERY" in location.get("c_locationPageServices", []), False)
        apply_yes_no(Extras.WIFI, item, "WIFI" in location.get("c_locationPageServices", []), False)
        apply_yes_no(
            PaymentMethods.AMERICAN_EXPRESS, item, "AMERICANEXPRESS" in location.get("paymentOptions", []), False
        )
        apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "DISCOVER" in location.get("paymentOptions", []), False)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "MASTERCARD" in location.get("paymentOptions", []), False)
        apply_yes_no(PaymentMethods.VISA, item, "VISA" in location.get("paymentOptions", []), False)
        item["extras"].pop("contact:instagram", None)
        item.pop("twitter", None)
        yield item
