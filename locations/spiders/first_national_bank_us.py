from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.yext_answers import YextAnswersSpider


class FirstNationalBankUSSpider(YextAnswersSpider):
    name = "first_national_bank_us"
    item_attributes = {"brand": "First National Bank", "brand_wikidata": "Q5426765"}
    api_key = "10f82fdf7a37ee369b154241c59dade1"
    experience_key = "fnb-answers"

    def parse_item(self, location, item):
        if location["data"]["type"] == "atm":
            apply_category(Categories.ATM, item)
        elif location["data"]["type"] == "location":
            apply_category(Categories.BANK, item)
            if amenities := location["data"].get("c_branchFilters"):
                apply_yes_no(Extras.ATM, item, "ATM" in amenities, False)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in amenities, False)
        else:
            self.logger.error("Unknown location type: {}".format(location["data"]["type"]))
        yield item
