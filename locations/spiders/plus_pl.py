from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PlusPLSpider(Spider):
    name = "plus_pl"
    start_urls = ["https://api.plus.pl/file/files/file/pos/cyfrowyplus.json"]
    item_attributes = {"brand": "Plus", "brand_wikidata": "Q7205598"}

    def parse(self, response, **kwargs):
        for feature in response.json()["apss"]["aps"]:
            item = DictParser.parse(feature)
            item["lat"], item["lon"] = feature["coords"].split(", ")
            weekRange = feature["businessHoursWeek"].split("-")
            satRange = feature["businessHoursWeekend"].split("-")
            sunRange = feature["businessHoursWeekendSunday"].split("-")
            item["opening_hours"] = OpeningHours()
            if len(weekRange) == 2:
                item["opening_hours"].add_days_range(
                    days=DAYS[:5], open_time=weekRange[0].strip(), close_time=weekRange[1].strip()
                )
            if len(satRange) == 2:
                item["opening_hours"].add_range(day="Sa", open_time=satRange[0].strip(), close_time=satRange[1].strip())
            if len(sunRange) == 2:
                item["opening_hours"].add_range(day="Su", open_time=sunRange[0].strip(), close_time=sunRange[1].strip())
            yield item
