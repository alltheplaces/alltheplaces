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
            week_range = feature["businessHoursWeek"].split("-")
            sat_range = feature["businessHoursWeekend"].split("-")
            sun_range = feature["businessHoursWeekendSunday"].split("-")
            item["opening_hours"] = OpeningHours()
            if len(week_range) == 2:
                item["opening_hours"].add_days_range(
                    days=DAYS[:5], open_time=week_range[0].strip(), close_time=week_range[1].strip()
                )
            if len(sat_range) == 2:
                item["opening_hours"].add_range(
                    day="Sa", open_time=sat_range[0].strip(), close_time=sat_range[1].strip()
                )
            if len(sun_range) == 2:
                item["opening_hours"].add_range(
                    day="Su", open_time=sun_range[0].strip(), close_time=sun_range[1].strip()
                )
            yield item
