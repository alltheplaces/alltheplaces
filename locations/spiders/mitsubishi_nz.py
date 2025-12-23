from copy import deepcopy
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class MitsubishiNZSpider(Spider):
    name = "mitsubishi_nz"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mmnz.co.nz/api/dealers"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for dealer in response.json():
            item = DictParser.parse(dealer)
            item["street"] = dealer["addressOne"]
            item["city"] = dealer["addressTwo"]
            item["state"] = dealer["location"]
            item["website"] = "https://www.mmnz.co.nz/" + dealer["link"]
            item["lat"] = dealer["locationY"]
            item["lon"] = dealer["locationX"]
            for dept in dealer["services"].split(","):
                if dept == "new":
                    sales_item = item.deepcopy()
                    sales_item["ref"] = str(sales_item["ref"]) + "-SALES"
                    sales_item["opening_hours"] = self.parse_opening_hours(dealer["salesOpeningHours"])
                    apply_category(Categories.SHOP_CAR, sales_item)
                    yield sales_item
                elif dept == "service":
                    service_item = item.deepcopy()
                    service_item["ref"] = str(service_item["ref"]) + "-SERVICE"
                    service_item["opening_hours"] = self.parse_opening_hours(dealer["serviceOpeningHours"])
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item
                elif dept == "parts":
                    spare_parts_item = item.deepcopy()
                    spare_parts_item["ref"] = str(spare_parts_item["ref"]) + "-SPARE_PARTS"
                    apply_category(Categories.SHOP_CAR_PARTS, spare_parts_item)
                    yield spare_parts_item

    def parse_opening_hours(self, opening_hours: list):
        oh = OpeningHours()
        for day_time in opening_hours:
            open_time = str(day_time["opens"])[:-2] + ":" + str(day_time["opens"])[-2:]
            close_time = str(day_time["closes"])[:-2] + ":" + str(day_time["closes"])[-2:]
            day = day_time["title"]
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        return oh
