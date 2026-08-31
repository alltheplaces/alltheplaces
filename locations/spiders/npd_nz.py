from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class NpdNZSpider(StockistSpider):
    name = "npd_nz"
    item_attributes = {"brand": "npd", "brand_wikidata": "Q110922616"}
    key = "u8329"

    def parse_item(self, item, location):
        apply_category(Categories.FUEL_STATION, item)
        item["branch"] = item.pop("name").removeprefix("NPD ").strip()
        if "Opening Soon" in item["branch"]:
            return
        item["website"] = location["custom_fields"][0]["value"]
        if item["email"] == "info@npd.co.nz":
            item["email"] = ""
        if phone := item["phone"]:
            if phone.replace(" ", "") == "08005446162":
                item["phone"] = ""
        if "24/7" in location["custom_fields"][1]["value"]:
            item["opening_hours"] = "24/7"
        elif "Opening Soon" in location["custom_fields"][1]["value"]:
            return
        elif location["custom_fields"][1]["value"] in ["461462", "392674", "457966"]:
            # observed gibberish values
            pass
        else:
            item["opening_hours"] = OpeningHours()
            if rules := location["custom_fields"][1]["value"]:
                ruleset = rules.replace("Everyday", "Mo-Su").replace("Sat & Sun", "Sa-Su").split(",")
                for rules in ruleset:
                    item["opening_hours"].add_ranges_from_string(rules)

        apply_yes_no(Fuel.DIESEL, item, any("Diesel" == filter["name"] for filter in location["filters"]))
        apply_yes_no(Fuel.OCTANE_91, item, any("Regular 91" == filter["name"] for filter in location["filters"]))
        apply_yes_no(Fuel.OCTANE_95, item, any("Premium 95" == filter["name"] for filter in location["filters"]))
        apply_yes_no(
            Fuel.OCTANE_100, item, any("100Plus High Octane" == filter["name"] for filter in location["filters"])
        )
        apply_yes_no(Fuel.ADBLUE, item, any(filter["name"] in ["AdBlue", "GoClear"] for filter in location["filters"]))
        apply_yes_no(Fuel.ELECTRIC, item, any("EV Charging" == filter["name"] for filter in location["filters"]))
        apply_yes_no(Fuel.LPG, item, any("LPG" in filter["name"] for filter in location["filters"]))

        apply_yes_no(Extras.CAR_WASH, item, any("Car Wash" == filter["name"] for filter in location["filters"]))
        apply_yes_no("food", item, any("Refresh Cafe" == filter["name"] for filter in location["filters"]))
        apply_yes_no(
            PaymentMethods.CONTACTLESS, item, any("PayWave" == filter["name"] for filter in location["filters"])
        )

        yield item
