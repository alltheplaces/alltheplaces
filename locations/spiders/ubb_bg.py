import re
import logging

from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_BG, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.user_agents import FIREFOX_LATEST


class UbbBGSpider(Spider):
    name = "ubb_bg"
    item_attributes = {"brand": "Обединена българска банка", "brand_wikidata": "Q7887555"}
    start_urls = ["https://www.ubb.bg/offices/pins"]
    user_agent = FIREFOX_LATEST
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        logging.info(response.body)
        try:
            markers = response.json()["markers"]
        except json.decoder.JSONDecodeError:
            logging.error("Invalid JSON response")
            return
        for location in markers["offices"]:
            item = Feature()
            item["ref"] = location["data"]["id"]
            item["lat"] = location["latlng"][0]
            item["lon"] = location["latlng"][1]
            item["name"] = location["data"]["title"]
            item["addr_full"] = location["data"]["address"]
            item["phone"] = location["data"]["phone"].replace("/", "").replace(",", ";")

            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.WHEELCHAIR, item, location["data"]["has_accessibility"])

            for feature in location["data"]["features"]:
                if feature["slug"] == "branch-of-former-kbc-bank":
                    item["brand"] = "ОББ*"
                    item["brand_wikidata"] = "Q7283808"

            item["opening_hours"] = OpeningHours()
            worktimes = (
                location["data"]["worktime"]
                .replace(";", ",")
                .replace("–", "-")
                .replace(" ", "")
                .replace("-", "")
                .replace("Пт", "Пет")
                .replace("Сб", "Съб")
                .replace("Нд", "Нед")
                .replace("Понеделник", "Пон")
                .replace("Неделя", "Нед")
                .split(".,")
            )
            for worktime in worktimes:
                worktime = worktime.replace(".", "").replace(",", "")
                if worktime == "":
                    continue

                hourhour_hourhour_dayday_regex = (
                    r"^(\d\d?:\d{2})(\d{2}:\d{2})(\d{2}:\d{2})(\d{2}:\d{2})([а-я]{3})([а-я]{3})$"
                )
                hourhour_dayday_regex = r"^(\d\d?:\d{2})(\d{2}:\d{2})([а-яА-Я]{3})([а-яА-Я]{3})$"
                hourhour_day_regex = r"^(\d{2}:\d{2})(\d{2}:\d{2})([а-я]{3})$"

                if matches := re.match(hourhour_hourhour_dayday_regex, worktime, re.IGNORECASE):
                    # hour-hour hour-hour day-day
                    # includes lunch break
                    start_time_1 = matches.group(1)
                    end_time_1 = matches.group(2)
                    start_time_2 = matches.group(3)
                    end_time_2 = matches.group(4)
                    start_day = sanitise_day(matches.group(5), DAYS_BG)
                    end_day = sanitise_day(matches.group(6), DAYS_BG)
                    item["opening_hours"].add_days_range(day_range(start_day, end_day), start_time_1, end_time_1)
                    item["opening_hours"].add_days_range(day_range(start_day, end_day), start_time_2, end_time_2)
                elif matches := re.match(hourhour_dayday_regex, worktime, re.IGNORECASE):
                    # hour-hour day-day
                    start_time = matches.group(1)
                    end_time = matches.group(2)
                    start_day = sanitise_day(matches.group(3), DAYS_BG)
                    end_day = sanitise_day(matches.group(4), DAYS_BG)
                    item["opening_hours"].add_days_range(day_range(start_day, end_day), start_time, end_time)
                elif matches := re.match(hourhour_day_regex, worktime, re.IGNORECASE):
                    # hour-hour day
                    start_time = matches.group(1)
                    end_time = matches.group(2)
                    day = sanitise_day(matches.group(3), DAYS_BG)
                    item["opening_hours"].add_range(day, start_time, end_time)
            yield item
        for location in markers["atms"]:
            item = Feature()
            item["ref"] = location["data"]["id"]
            item["addr_full"] = location["data"]["address"]
            item["lat"] = location["latlng"][0]
            item["lon"] = location["latlng"][1]

            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.WHEELCHAIR, item, location["data"]["has_accessibility"])

            has_cash_in = False
            for feature in location["data"]["features"]:
                if feature["slug"] == "kbc-bank-atm":
                    item["brand"] = "ОББ*"
                    item["brand_wikidata"] = "Q7283808"
                if feature["slug"] == "atm-money-deposit":
                    has_cash_in = True
                if feature["slug"] == "day-and-night-access":
                    item["opening_hours"] = "24/7"
            apply_yes_no(Extras.CASH_IN, item, has_cash_in)
            yield item
