from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingEELTLVSpider(JSONBlobSpider):
    name = "burger_king_ee_lt_lv"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    # en to make parsing hours easier, nothing else appears to change between languages
    start_urls = ["https://www.burgerking.ee/page-data/en/restaurants/page-data.json"]
    no_refs = True
    locations_key = ["result", "data", "allFile", "edges", 0, "node", "childTranslationsJson", "restaurants"]

    def post_process_item(self, item, response, location):
        item["branch"] = location["heading"].replace("Burger King ", "")
        item["addr_full"] = clean_address(location["addressLines"])
        item["opening_hours"] = OpeningHours()
        if "drive-thru" in location["workingHours"].lower():
            hours, drive_through_hours = location["workingHours"].lower().split("drive-thru", 1)
            for day in DAYS_3_LETTERS:
                day = day.lower()
                drive_through_hours = drive_through_hours.replace(f"{day}.", day)
            o = OpeningHours()
            o.add_ranges_from_string(drive_through_hours)
            item["extras"]["opening_hours:drive_through"] = o.as_opening_hours()
        else:
            hours = location["workingHours"].lower()
        for day in DAYS_3_LETTERS:
            day = day.lower()
            hours = hours.replace(f"{day}.", day)
        item["opening_hours"].add_ranges_from_string(hours)
        yield item
