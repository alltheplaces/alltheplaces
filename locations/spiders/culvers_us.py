from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class CulversUSSpider(Where2GetItSpider):
    name = "culvers_us"
    item_attributes = {"brand": "Culver's", "brand_wikidata": "Q1143589"}
    api_brand_name = "culvers"
    api_key = "1099682E-D719-11E6-A0C4-347BDEB8F1E5"
    api_filter = {"number": {"ne": "P"}}

    def parse_item(self, item, location):
        item["branch"] = item.pop("name").removeprefix("Culver's of ")
        item["website"] = item["website"].replace("http://", "https://")

        item["opening_hours"] = OpeningHours()
        for day in ["mon", "tues", "wed", "thurs", "fri", "sat", "sun"]:
            item["opening_hours"].add_range(
                day, location["{}openfrom".format(day)], location["{}opento".format(day)], "%I:%M %p"
            )

        apply_yes_no(Extras.INDOOR_SEATING, item, location["dine_in"] == "1", False)
        apply_yes_no(Extras.TAKEAWAY, item, location["takeout"] == "1", False)
        apply_yes_no(Extras.DELIVERY, item, location["delivery"] == "1", False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["drivethru"] == "1", False)
        apply_yes_no(Extras.TOILETS, item, location["restroom"] == "1", False)
        apply_yes_no(PaymentMethods.VISA, item, location["visa"] == "1", False)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, location["mastercard"] == "1", False)

        if location["drivethru"] == "1":
            oh = OpeningHours()
            for day in ["mon", "tues", "wed", "thurs", "fri", "sat", "sun"]:
                oh.add_range(
                    day, location["dt_{}openfrom".format(day)], location["dt_{}opento".format(day)], "%I:%M %p"
                )
            item["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()

        yield item
