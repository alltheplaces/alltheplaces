import re

from locations.hours import DAYS, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class TimberlandSpider(Where2GetItSpider):
    name = "timberland"
    item_attributes = {"brand": "Timberland", "brand_wikidata": "Q1539185"}
    api_brand_name = "timberland"
    api_key = "478C75E0-34A6-11E5-BDEC-1E25B945EC6E"
    api_filter = {"icon": {"in": "retail,factory,Timberland_Store,Timberland_Outlet_Store,default"}}

    def parse_item(self, item, location):
        if location.get("enterprise_store_identifier"):
            item["ref"] = location.get("enterprise_store_identifier")
        item["name"] = item["name"].replace("&reg", "").replace(";", "").replace("TIMBERLAND", "Timberland")
        item["name"] = re.sub(r" {2,}", " ", item["name"])
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        hours_string = ""
        for day in list(zip(["m", "t", "w", "thu", "f", "sa", "su"], DAYS)):
            if location.get(day[0]):
                hours_string = f"{hours_string} {day[1]}: " + location.get(day[0]).replace("/", ",")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
