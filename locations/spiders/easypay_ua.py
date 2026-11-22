from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EasypayUASpider(JSONBlobSpider):
    name = "easypay_ua"
    item_attributes = {"brand": "EasyPay", "brand_wikidata": "Q4037884", "name": "EasyPay"}
    start_urls = ["https://tech.easypay.ua/api/terminal/map?isFullData=true"]
    locations_key = "terminals"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["status"] != "Active":
            return
        item["ref"] = feature["terminalId"]
        # The name is the shop or building hosting the terminal
        item["located_in"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["state"] = feature["regionName"]

        if feature["schedule"]:
            item["opening_hours"] = OpeningHours()
            for day in feature["schedule"]:
                if day["schedule"] == "0":
                    item["opening_hours"].set_closed(DAYS[day["dayOfTheWeek"]])
                else:
                    item["opening_hours"].add_range(DAYS[day["dayOfTheWeek"]], *day["schedule"].split("-"))

        apply_category(Categories.PAYMENT_TERMINAL, item)
        yield item
