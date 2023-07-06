from locations.hours import OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class MoneyGramSpider(Where2GetItSpider):
    name = "moneygram"
    item_attributes = {"brand": "MoneyGram", "brand_wikidata": "Q1944412"}
    api_brand_name = "moneygram"
    api_key = "46493320-D5C3-11E1-A25A-4A6F97B4DA77"
    separate_api_call_per_country = True

    def parse_item(self, item, location):
        hours_string = ""
        for day_name in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            if location.get(day_name + "_hours"):
                hours_string = f"{hours_string} {day_name}: " + location.get(day_name + "_hours")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
