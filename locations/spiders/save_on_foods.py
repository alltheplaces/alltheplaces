import re

import scrapy

from locations.items import Feature


class SaveOnFoodsSpider(scrapy.Spider):
    name = "save_on_foods"
    item_attributes = {"brand": "Save on Foods"}
    allowed_domains = ["shop.saveonfoods.com"]

    def start_requests(self):
        urls = [
            "https://shop.saveonfoods.com/api/stores/v7/chains/8E4E398/stores?_=1513711317679&skip=0&take=999&region=AB",
            "https://shop.saveonfoods.com/api/stores/v7/chains/8E4E398/stores?_=1513711463381&skip=0&take=999&region=BC",
            "https://shop.saveonfoods.com/api/stores/v7/chains/8E4E398/stores?_=1513711463388&skip=0&take=999&region=MB",
            "https://shop.saveonfoods.com/api/stores/v7/chains/8E4E398/stores?_=1513711463389&skip=0&take=999&region=SK",
            "https://shop.saveonfoods.com/api/stores/v7/chains/8E4E398/stores?_=1513711463390&skip=0&take=999&region=YT",
        ]

        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.kfc.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://shop.saveonfoods.com/store/DF191211/?_ga=1.168908327.789228674.1484454975/",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Authorization": "59b1ced8-4cbe-4615-accc-69b2b7df780a",
            "Host": "shop.saveonfoods.com",
        }

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def normalize_time(self, time_str):
        match = re.search(r"(\d{1,2}):(\d{2})([AP])M", time_str)
        h, m, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "P" else int(h),
            int(m),
        )

    def store_hours(self, store_hours):
        opening_hours = []
        for day_hours in store_hours:
            day_hours = (
                day_hours.replace("Monday", "Mo")
                .replace("Tuesday", "Tu")
                .replace("Wednesday", "We")
                .replace("Thursday", "Th")
                .replace("Friday", "Fr")
                .replace("Saturday", "Sa")
                .replace("Sunday", "Su")
            )
            day_hours = (
                day_hours.replace("Weekdays", "Mo-Fr")
                .replace("Weekends", "Sa-Su")
                .replace("Holidays", "PH")
                .replace("Everyday", "Mo-Su")
            )
            day_hours = day_hours.replace("midnight", "12 PM")

            hours = ""
            match = re.search(r"(\d{1,2}) (A|P)M -(\d{1,2}) (A|P)M", day_hours)
            if match:
                (f_hr, f_ampm, t_hr, t_ampm) = match.groups()
                f_hr = int(f_hr)
                if f_ampm == "P":
                    f_hr += 12
                elif f_ampm == "A" and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm == "P":
                    t_hr += 12
                elif t_ampm == "A" and t_hr == 12:
                    t_hr = 0

                hours = "{:02d}:{}-{:02d}:{}".format(
                    f_hr,
                    "00",
                    t_hr,
                    "00",
                )
                day_hours = day_hours.replace(match.group(), hours)
                opening_hours.append(day_hours)
            else:
                match = re.search(r"(\d{1,2}):(\d{2}) (A|P)M-(\d{1,2}):(\d{2}) (A|P)M", day_hours)
                if match:
                    (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()
                    f_hr = int(f_hr)
                    if f_ampm == "P":
                        f_hr += 12
                    elif f_ampm == "A" and f_hr == 12:
                        f_hr = 0
                    t_hr = int(t_hr)
                    if t_ampm == "P":
                        t_hr += 12
                    elif t_ampm == "A" and t_hr == 12:
                        t_hr = 0

                    hours = "{:02d}:{}-{:02d}:{}".format(
                        f_hr,
                        f_min,
                        t_hr,
                        t_min,
                    )
                    day_hours = day_hours.replace(match.group(), hours)
                opening_hours.append(day_hours)
        return "; ".join(opening_hours)

    def parse(self, response):
        data = response.json()
        for item in data["Stores"]:
            store = item["Sections"][0]
            store_properties = {
                "ref": "{}_store".format(item["Id"]),
                "name": store["Name"],
                "addr_full": store["Address"]["AddressLine1"],
                "city": store["Address"]["City"],
                "state": store["Address"]["Region"],
                "postcode": store["Address"]["PostalCode"],
                "lat": store["Coordinates"]["Latitude"],
                "lon": store["Coordinates"]["Longitude"],
                "phone": store["Phone"],
                "opening_hours": self.store_hours(store["SectionSchedule"]),
            }
            yield Feature(**store_properties)

            if len(item["Sections"]) > 1:
                pharmacy = item["Sections"][1]
                pharmacy_properties = {
                    "ref": "{}_pharmacy".format(item["Id"]),
                    "name": pharmacy["Name"],
                    "addr_full": pharmacy["Address"]["AddressLine1"],
                    "city": pharmacy["Address"]["City"],
                    "state": pharmacy["Address"]["Region"],
                    "postcode": pharmacy["Address"]["PostalCode"],
                    "lat": pharmacy["Coordinates"]["Latitude"],
                    "lon": pharmacy["Coordinates"]["Longitude"],
                    "phone": pharmacy["Phone"],
                    "opening_hours": self.store_hours(pharmacy["SectionSchedule"]),
                }

                yield Feature(**pharmacy_properties)
