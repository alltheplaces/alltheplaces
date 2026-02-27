from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider

BRANDS = {
    "OfficeMax": {"brand": "OfficeMax", "brand_wikidata": "Q7079111"},
    "Office Depot": {"brand": "Office Depot", "brand_wikidata": "Q1337797"},
}


class OfficeDepotSpider(Where2GetItSpider):
    name = "office_depot"
    api_key = "592778B0-A13B-11EB-B3DB-84030D516365"

    def parse_item(self, item, location):
        item["name"] = location.get("lname")
        match location.get("icon"):
            case "officedepot":
                item.update(BRANDS["Office Depot"])
            case "officemax":
                item.update(BRANDS["OfficeMax"])
        item["image"] = location.get("location image").get("Image URL")
        hours_string = ""
        for day in DAYS_FULL:
            open_time = location.get(day.lower() + "_open")
            close_time = location.get(day.lower() + "_close")
            hours_string = hours_string + f" {day}: {open_time} - {close_time}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
