from datetime import datetime as dt
from zoneinfo import ZoneInfo

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


def unix_timestamp_to_local_time(timezone, timestamp):
    return dt.fromtimestamp(timestamp * 1e-3).astimezone(timezone).strftime("%H:%M")


class EcontBGSpider(Spider):
    name = "econt_bg"
    item_attributes = {"brand": "Econt", "brand_wikidata": "Q12279603"}
    allowed_domains = ["ee.econt.com"]
    start_urls = ["https://ee.econt.com/services/Nomenclatures/NomenclaturesService.getOffices.json"]

    def parse(self, response):
        for location in response.json()["offices"]:
            if location["address"]["city"]["country"]["code2"] != "BG":
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location["name"]
            item["city"] = location["address"]["city"]["name"]
            item["phone"] = ";".join(location["phones"])
            item["email"] = ";".join(location["emails"])
            item["addr_full"] = location["address"]["fullAddress"]
            item["street"] = location["address"]["street"]
            item["housenumber"] = location["address"]["num"]
            item["lat"] = location["address"]["location"]["latitude"]
            item["lon"] = location["address"]["location"]["longitude"]

            item["opening_hours"] = OpeningHours()

            if "24/7" in item["name"]:
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                timezone = ZoneInfo("Europe/Sofia")
                weekday_start_time = unix_timestamp_to_local_time(timezone, location["normalBusinessHoursFrom"])
                weekday_end_time = unix_timestamp_to_local_time(timezone, location["normalBusinessHoursTo"])
                item["opening_hours"].add_days_range(DAYS_WEEKDAY, weekday_start_time, weekday_end_time)

                if location["halfDayBusinessHoursFrom"] is not None:
                    saturday_start_time = unix_timestamp_to_local_time(timezone, location["halfDayBusinessHoursFrom"])
                    saturday_end_time = unix_timestamp_to_local_time(timezone, location["halfDayBusinessHoursTo"])
                    item["opening_hours"].add_range("Sa", saturday_start_time, saturday_end_time)

                if location["sundayBusinessHoursFrom"] is not None:
                    sunday_start_time = unix_timestamp_to_local_time(timezone, location["sundayBusinessHoursFrom"])
                    sunday_end_time = unix_timestamp_to_local_time(timezone, location["sundayBusinessHoursTo"])
                    item["opening_hours"].add_range("Su", sunday_start_time, sunday_end_time)

            if location["isAPS"]:
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                apply_category(Categories.POST_OFFICE, item)

            yield item
