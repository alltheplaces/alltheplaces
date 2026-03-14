import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class HyundaiATSpider(scrapy.Spider):
    name = "hyundai_at"
    item_attributes = {"brand": "Hyundai", "brand_wikidata": "Q55931"}
    start_urls = ["https://www.hyundai.at/partner-finden/"]

    def parse(self, response, **kwargs):
        raw_data = json.loads(
            re.search(
                r"\"data\":({.*}),\"pageCount",
                response.xpath('//*[contains(text(),"displayName")]/text()').get().replace("\\", "").replace("`", ""),
            ).group(1)
        )
        for location in raw_data.values():
            for dealer in location:
                item = DictParser.parse(dealer)
                item["name"] = dealer.get("displayName")
                item["postcode"] = dealer.get("plz")
                item["street_address"] = item["ref"] = item.pop("street")
                item["city"] = dealer.get("ort")
                item["state"] = dealer.get("bundeslandcd")
                item["lat"] = item["lat"].replace(",", ".")
                item["lon"] = item["lon"].replace(",", ".")
                if item.get("website") and "http" not in item.get("website"):
                    item["website"] = "https://" + item["website"]

                if dealer.get("verkauf"):
                    sales_item = item.deepcopy()
                    sales_item["ref"] = sales_item["ref"] + "-SALES"
                    apply_category(Categories.SHOP_CAR, sales_item)
                    item["opening_hours"] = self.parse_opening_hours(dealer.get("verkaufOeffnungszeitenDisplay"))
                    yield sales_item
                if dealer.get("werkstatt"):
                    service_item = item.deepcopy()
                    service_item["ref"] = service_item["ref"] + "-SERVICE"
                    item["opening_hours"] = self.parse_opening_hours(dealer.get("werkstattOeffnungszeitenDisplay"))
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item

    def parse_opening_hours(self, hours_data_list: list):
        oh = OpeningHours()
        try:
            for raw_day_time in hours_data_list:
                for day_time in raw_day_time:
                    day = sanitise_day(day_time["dayShort"], DAYS_DE)
                    for open_close_time in day_time["timeRange"].split(","):
                        open_time, close_time = open_close_time.split("-")
                        oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
            return oh
        except:
            pass
