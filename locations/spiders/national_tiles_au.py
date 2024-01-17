from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NationalTilesAUSpider(Spider):
    name = "national_tiles_au"
    item_attributes = {"brand": "National Tiles", "brand_wikidata": "Q117157007"}
    allowed_domains = ["www.nationaltiles.com.au"]
    start_urls = ["https://www.nationaltiles.com.au/tradepdp/index/getstoredetails/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json()["output"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["state"] = location["region"]["region"]
            item["website"] = location["canonical_url"]

            if location.get("schedule_array"):
                oh = OpeningHours()
                for day_name, day in location["schedule_array"].items():
                    if day[f"{day_name}_status"] != "1":
                        continue
                    open_time = day["from"]["hours"] + ":" + day["from"]["minutes"]
                    break_start = day["break_from"]["hours"] + ":" + day["break_from"]["minutes"]
                    break_end = day["break_to"]["hours"] + ":" + day["break_to"]["minutes"]
                    close_time = day["to"]["hours"] + ":" + day["to"]["minutes"]
                    if break_start == break_end:
                        oh.add_range(day_name.title(), open_time, close_time)
                    else:
                        oh.add_range(day_name.title(), open_time, break_start)
                        oh.add_range(day_name.title(), break_end, close_time)
                item["opening_hours"] = oh.as_opening_hours()

            yield item
