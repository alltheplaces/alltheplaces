from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class StarbucksHKMO(JSONBlobSpider):
    name = "starbucks_hk_mo"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    start_urls = ["https://www.starbucks.com.hk/rest/V1/mxstarbucks-getSBStoreList"]
    needs_json_request = True
    locations_key = "data"

    def post_process_item(self, item, response, location):
        if location["locates_hk_or_mc"] == "Hong Kong":
            item["country"] = "HK"
        elif location["locates_hk_or_mc"] == "Macau":
            item["country"] = "MO"

        item["extras"]["branch:en"] = location["name_en"]
        item["extras"]["branch:zh"] = location["name_cn"]
        item["branch"] = item["extras"]["branch:zh"] + " " + item["extras"]["branch:en"]

        item["extras"]["addr:full:en"] = location["address1_en"]
        item["extras"]["addr:full:zh"] = location["address1_cn"]
        item["addr_full"] = item["extras"]["addr:full:zh"] + " " + item["extras"]["addr:full:en"]

        apply_yes_no(Extras.WIFI, item, location["is_free_wifi"] == "1")
        apply_yes_no(Extras.TAKEAWAY, item, location["has_starbucks_take_away"] == "1")

        item["opening_hours"] = OpeningHours()
        if location["is24_hours"] == "1":
            item["opening_hours"] = "Mo-Su 00:00-24:00"
        else:
            for day in DAYS_3_LETTERS:
                day = day.lower()
                if day == "thu":
                    day = "thurs"
                if location["enable_mon"] == "0":
                    item["opening_hours"].set_closed(day)
                if location[f"{day}_is24_hour"] == "1":
                    item["opening_hours"].add_range(day, "00:00", "23:59")
                else:
                    item["opening_hours"].add_range(day, location[f"{day}_open_hour"], location[f"{day}_close_hour"])

        yield item
