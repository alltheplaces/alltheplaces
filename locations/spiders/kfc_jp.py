import json

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KFCJPSpider(Spider):
    name = "kfc_jp"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    allowed_domains = ["search.kfc.co.jp"]
    start_urls = ["https://search.kfc.co.jp/api/point?b=31,129,46,146"]

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["ref"] = location["key"]
            item["website"] = "https://search.kfc.co.jp/map/" + item["ref"]
            yield Request(url=item["website"], meta={"item": item}, callback=self.parse_hours)

    def parse_hours(self, response):
        item = response.meta["item"]
        data_raw = response.xpath('//div[@id="sl-root"]/script[not(@src)][1]/text()').get().split("\n")
        data_json = "{}"
        for constant in data_raw:
            if ".constant('CURRENT_POINT'" in constant:
                data_json = constant.split(".constant('CURRENT_POINT', ")[1][:-1]
                break
        location = json.loads(data_json)
        item2 = DictParser.parse(location)
        for key, value in item2.items():
            if value:
                item[key] = value

        oh = OpeningHours()
        day_ranges = {
            "平日営業時間": ["Mo", "Tu", "We", "Th", "Fr"],
            "土日祝営業時間": ["Sa", "Su"],
        }
        for range_name, days in day_ranges.items():
            if range_name not in location:
                continue
            if location[range_name] == "None" or not location[range_name]:
                continue
            for day in days:
                open_time = location[range_name].split("-")[0]
                close_time = location[range_name].split("-")[1]
                if len(open_time) == 4:  # HHMM should be HH:MM
                    open_time = open_time[:2] + ":" + open_time[:-2]
                elif len(open_time) != 5:  # HH:MM expected
                    break
                if len(close_time) == 4:  # HHMM should be HH:MM
                    close_time = close_time[:2] + ":" + close_time[:-2]
                elif len(close_time) != 5:  # HH:MM expected
                    break
                oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh.as_opening_hours()

        yield item
