import json
from datetime import datetime
from zoneinfo import ZoneInfo

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

STATE_TIMEZONES = {
    "Australian Capital Territory": "Australia/Sydney",
    "New South Wales": "Australia/Sydney",
    "Northern Territory": "Australia/Darwin",
    "Queensland": "Australia/Brisbane",
    "South Australia": "Australia/Adelaide",
    "Tasmania": "Australia/Hobart",
    "Victoria": "Australia/Melbourne",
    "Western Australia": "Australia/Perth",
}


class FortyWinksAUSpider(Spider):
    name = "forty_winks_au"
    item_attributes = {"brand": "Forty Winks", "brand_wikidata": "Q106283438"}
    allowed_domains = ["fortywinks-prod.azure-api.net"]
    start_urls = ["https://fortywinks-prod.azure-api.net/store-app/stores?storeUrl=undefined"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["key"]
            item["street_address"] = location["address"]["address"].replace(" , ", ", ")
            if item["website"]:
                item["website"] = "https://www.fortywinks.com.au/store-finder" + item["website"]
            time_zone = ZoneInfo(STATE_TIMEZONES[item["state"]])
            item["opening_hours"] = OpeningHours()
            hours_dict = {}
            for hours_raw in location["openingHours"]:
                hours_json = json.loads(hours_raw)
                hours_dict.update(hours_json)
            for day_name, hours_ranges in hours_dict.items():
                if not day_name:
                    specified_day_names = list(filter(None, hours_dict.keys()))
                    missing_day_names = list(set(DAYS_FULL) - set(specified_day_names))
                    if len(missing_day_names) == 1:
                        day_name = missing_day_names[0]
                    else:
                        self.logger.error(
                            "Multiple missing day names in provided opening hours. Extracted opening hours data will be partially incomplete."
                        )
                        continue
                for hours_range in hours_ranges:
                    if not hours_range["Start"] or not hours_range["Finish"]:
                        continue
                    open_time = datetime.fromisoformat(hours_range["Start"]).astimezone(time_zone).strftime("%H:%M")
                    close_time = datetime.fromisoformat(hours_range["Finish"]).astimezone(time_zone).strftime("%H:%M")
                    item["opening_hours"].add_range(day_name, open_time, close_time)
            yield item
