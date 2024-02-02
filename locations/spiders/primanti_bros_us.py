from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class PrimantiBrosUSSpider(Where2GetItSpider):
    name = "primanti_bros_us"
    item_attributes = {"brand": "Primanti Bros", "brand_wikidata": "Q7243049"}
    api_brand_name = "primantibros"
    api_key = "7CDBB1A2-4AC6-11EB-932C-8917919C4603"

    def parse_item(self, item, location):
        item["ref"] = location["uid"]
        item["street_address"] = ", ".join(filter(None, [location.get("address1"), location.get("address2")]))
        item["website"] = location.get("menuurl")
        item["opening_hours"] = OpeningHours()
        hours_string = ""
        for day_name in DAYS_FULL:
            hours_string = f"{hours_string} {day_name}: " + location["{}hours".format(day_name.lower())]
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["has_drive_through"] == "1", False)
        yield item
