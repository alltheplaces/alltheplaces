from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.where2getit import Where2GetItSpider


class FamilyDollarUSSpider(Where2GetItSpider):
    name = "family_dollar_us"
    item_attributes = {"brand": "Family Dollar", "brand_wikidata": "Q5433101"}
    api_brand_name = "familydollar"
    api_key = "D2F68B64-7E11-11E7-B734-190193322438"
    api_filter = {
        "and": {
            "distributioncenter": {"distinctfrom": "1"},
            "bopis": {"eq": ""},
            "tobacco": {"eq": ""},
            "adult_beverages": {"eq": ""},
            "propane": {"eq": ""},
            "red_box": {"eq": ""},
            "ebt": {"eq": ""},
            "atm": {"eq": ""},
            "ice": {"eq": ""},
            "water_machine": {"eq": ""},
            "refrigerated_frozen": {"eq": ""},
            "helium": {"eq": ""},
            "fresh_produce": {"eq": ""},
            "billpay": {"eq": ""},
        }
    }

    def parse_item(self, item, location):
        if location["coming_soon"] == "Y" or location["temp_closed"] == "Y" or location["temporarily_closed"] == "Y":
            return
        item["street_address"] = clean_address([location["address1"], location["address2"]])
        item["website"] = (
            "https://www.familydollar.com/locations/"
            + item["state"].lower()
            + "/"
            + item["city"].lower().replace(" ", "-")
            + "/"
            + item["ref"]
            + "/"
        )
        hours_string = ""
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            open_time = location.get(day.lower() + "open")
            close_time = location.get(day.lower() + "close")
            hours_string = hours_string + f" {day}: {open_time} - {close_time}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        item["extras"]["ref:branch"] = item.pop("name", "").removeprefix("FAMILY DOLLAR #")
        yield item
