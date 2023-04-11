from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class CulversUSSpider(Where2GetItSpider):
    name = "culvers_us"
    item_attributes = {"brand": "Culver's", "brand_wikidata": "Q1143589"}
    api_brand_name = "culvers"
    api_key = "1099682E-D719-11E6-A0C4-347BDEB8F1E5"
    api_filter = {
        "number": {"ne": "P"}
    }

    def parse_item(self, item, location):
        item["opening_hours"] = OpeningHours()
        for day_index in range(-1, 5, 1):
            item["opening_hours"].add_range(DAYS[day_index], location["bho"][day_index + 1][0], location["bho"][day_index + 1][1], "%H%M")
        apply_yes_no(Extras.INDOOR_SEATING, item, location["dine_in"], False)
        apply_yes_no(Extras.TAKEAWAY, item, location["takeout"], False)
        apply_yes_no(Extras.DELIVERY, item, location["delivery"], False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["drivethru"], False)
        apply_yes_no(Extras.TOILETS, item, location["restroom"], False)
        apply_yes_no(PaymentMethods.VISA, item, location["visa"], False)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, location["mastercard"], False)
        yield item
