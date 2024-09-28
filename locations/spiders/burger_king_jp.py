from scrapy.http import Request

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingJPSpider(JSONBlobSpider):
    download_timeout = 30
    name = "burger_king_jp"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerking.co.jp/BKJ0001.json"]
    locations_key = ["body", "storeList"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
                body='message={"header":{"error_code":"","error_text":"","info_text":"","login_session_id":"","message_version":"","ip_address":"","result":true,"trcode":"BKJ0001","platform":"02","id_member":"","auth_token":""},"body":{"state":"","city":"","dirveTh":"","dlvyn":"","kmonYn":"","kordYn":"","oper24Yn":"","parkingYn":"","wifiYn":"","powerYn":"","distance":"1000","sortType":"DISTANCE","storCoordX":"136","storCoordY":"35","storNm":""}}',
            )

    def post_process_item(self, item, response, location):
        item["ref"] = location["STOR_CD"]
        item["lat"] = location["STOR_COORD_Y"]
        item["lon"] = location["STOR_COORD_X"]
        item["branch"] = location["STOR_NM"]
        item["street_address"] = location["ADDR_1"]
        item["addr_full"] = clean_address([location["ADDR_1"], location["ADDR_2"]])
        apply_yes_no(Extras.WIFI, item, location["WIFI_YN"] == "1")
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["DIRVE_TH"] == "1", False)
        apply_yes_no(Extras.DELIVERY, item, location["DLVYN"] == "1", False)

        item["opening_hours"] = OpeningHours()
        try:
            item["opening_hours"].add_days_range(
                DAYS_WEEKDAY, location["WEEKDAY_START_HOUR"], location["WEEKDAY_FNSH_HOUR"], time_format="%H%M"
            )
            item["opening_hours"].add_range(
                "Sat", location["WEEKEND_START_HOUR"], location["WEEKEND_FNSH_HOUR"], time_format="%H%M"
            )
            item["opening_hours"].add_range(
                "Sun", location["HOLIDAY_START_HOUR"], location["HOLIDAY_FNSH_HOUR"], time_format="%H%M"
            )
        except ValueError:
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")

        yield item
