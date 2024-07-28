import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours


class RosselkhozbankRUSpider(scrapy.Spider):
    name = "rosselkhozbank_ru"
    item_attributes = {"brand_wikidata": "Q3920226"}

    def start_requests(self):
        yield JsonRequest("https://www.rshb.ru/api/v1/regions", callback=self.parse_regions)

    def parse_regions(self, response):
        for region in response.json():
            yield JsonRequest(
                f"https://www.rshb.ru/api/v1/branchesAndRemoteWorkplaces?regionCode={region['code']}",
            )

    def parse(self, response):
        for poi in response.json()["branches"]:
            item = DictParser.parse(poi)
            item["branch"] = item.pop("name")
            item["lat"], item["lon"] = poi.get("gpsLatitude"), poi.get("gpsLongitude")
            self.parse_hours(item, poi)
            apply_category(Categories.BANK, item)
            yield item

    def parse_hours(self, item, poi):
        time_format = "%H.%M"
        no_break = "Без перерыва"

        def _handle_weekday_hours(oh, work_schedule):
            work_time = work_schedule.get("workTime")
            lunch_hour = work_schedule.get("lunchHour")
            if not work_time:
                return

            if not lunch_hour or lunch_hour.strip() == no_break:
                open_time, close_time = work_time.split("–")
                oh.add_days_range(DAYS_WEEKDAY, open_time, close_time, time_format)
            else:
                open_time, close_time = work_time.split("–")
                open_lunch, close_lunch = lunch_hour.split("–")
                oh.add_days_range(DAYS_WEEKDAY, open_time, open_lunch, time_format)
                oh.add_days_range(DAYS_WEEKDAY, close_lunch, close_time, time_format)

        def _handle_saturday_hours(oh, work_schedule):
            work_time_saturday = work_schedule.get("workTimeSaturday")
            lunch_hour_saturday = work_schedule.get("lunchHourSaturday")
            if not work_time_saturday:
                return

            if not lunch_hour_saturday or lunch_hour_saturday.strip() == no_break:
                open_time, close_time = work_time_saturday.split("–")
                oh.add_range("Sa", open_time, close_time, time_format)
            else:
                open_time, close_time = work_time_saturday.split("–")
                open_lunch, close_lunch = lunch_hour_saturday.split("–")
                oh.add_range("Sa", open_time, open_lunch, time_format)
                oh.add_range("Sa", close_lunch, close_time, time_format)

        work_schedule = poi.get("workSchedule")
        if not work_schedule:
            return

        if not work_schedule.get("isMatchesPattern"):
            return

        try:
            oh = OpeningHours()
            _handle_weekday_hours(oh, work_schedule)
            _handle_saturday_hours(oh, work_schedule)
            item["opening_hours"] = oh.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {e}, {work_schedule}")
            self.crawler.stats.inc_value("atp/hours/failed")
