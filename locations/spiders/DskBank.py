import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.items import Feature


class DSKBankBGSpider(scrapy.Spider):
    name = "dsk_bank_bg"
    item_attributes = {"brand": "Банка ДСК", "brand_wikidata": "Q5206146"}
    allowed_domains = ["https://www.dskbank.bg/"]
    start_urls = ["https://dskbank.bg/контакти/клонова-мрежа/GetOffices/"]

    def parse(self, response):
        for data in response.json():
            item = Feature()
            item["ref"] = data["Id"]
            item["name"] = data["Name"]
            item["lat"] = data["Latitude"]
            item["lon"] = data["Longitude"]
            item["email"] = data["Email"]

            branch_type = data["BranchType"]
            if "Branch" in branch_type:
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)

            text = data["Text"]
            clean_text = re.sub(r"<.*?>", "\n", text)
            clean_text = re.sub("\n+", "\n", clean_text)
            clean_text = clean_text.strip("\n").split("\n")

            item["addr_full"] = clean_text[0]

            phone = data["Phone"]
            if phone:
                phone = re.sub(r"\(|\*|\|\);", "", phone)
            item["phone"] = phone

            OpenHours = data["OpenHours"]
            item["opening_hours"] = OpeningHours()
            if OpenHours:
                OpenHours = re.sub(r"<.*?>", ",", OpenHours)
                OpenHours = re.sub(r"\r\n", "", OpenHours)
                OpenHours = re.sub(r"-", " ", OpenHours)
                OpenHours = OpenHours.split(",")
                for i in OpenHours:
                    i = i.strip()
                    i = re.split(r"\s+", i)
                    if len(i) == 3:
                        day, hour_from, hour_to = i
                        if day in DAYS_BG:
                            hour_from = re.sub(r"\.", ":", hour_from)
                            hour_to = re.sub(r"\.", ":", hour_to)
                            hour_to += ":00"
                            hour_from += ":00"
                            item["opening_hours"].add_range(sanitise_day(day, DAYS_BG), hour_from, hour_to, "%H:%M:%S")
                    else:
                        pass
            else:
                item["opening_hours"] = None

            yield item
