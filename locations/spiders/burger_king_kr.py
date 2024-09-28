from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS, DAYS_KR, DELIMITERS_KR, NAMED_DAY_RANGES_KR, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingKRSpider(JSONBlobSpider):
    download_timeout = 60
    name = "burger_king_kr"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.co.kr/store/selectStore.json"]
    locations_key = ["body", "storeList"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["STOR_CD"]
        item["lat"] = location["STOR_COORD_Y"]
        item["lon"] = location["STOR_COORD_X"]
        item["branch"] = location["STOR_NM"]
        item["street_address"] = location["ADDR_1"]
        item["addr_full"] = clean_address([location["ADDR_1"], location["ADDR_2"]])
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["DIRVE_TH"] == "1", False)
        apply_yes_no(Extras.DELIVERY, item, location["DLVYN"] == "1", False)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            location["STORE_TIME"], days=DAYS_KR, named_day_ranges=NAMED_DAY_RANGES_KR, delimiters=DELIMITERS_KR
        )
        if location["DLVYN"] == "1":
            oh = OpeningHours()
            oh.add_days_range(DAYS, location["DLV_START_TIME"], location["DLV_FNSH_TIME"], time_format="%H%M")
            item["extras"]["opening_hours:delivery"] = oh.as_opening_hours()

        yield item
