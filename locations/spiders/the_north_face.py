from locations.hours import DAYS, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class TheNorthFaceSpider(Where2GetItSpider):
    name = "the_north_face"
    item_attributes = {"brand": "The North Face", "brand_wikidata": "Q152784"}
    api_brand_name = "northface"
    api_key = "C1907EFA-14E9-11DF-8215-BBFCBD236D0E"
    api_filter = {
        "or": {
            "northface": {"eq": "1"},
            "outletstore": {"eq": "1"}
        }
    }

    def parse_item(self, item, location):
        if location.get("enterprise_store_identifier"):
            item["ref"] = location.get("enterprise_store_identifier")
        if item["state"].upper() == "TNF RETAIL":
            item["state"] = None
        hours_string = ""
        for day in list(zip(["m", "t", "w", "thu", "f", "sa", "su"], DAYS)):
            if location.get(day[0]):
                hours_string = f"{hours_string} {day[1]}: " + location.get(day[0]).replace("/", ",")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
