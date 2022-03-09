# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class HolidayStationstoreSpider(scrapy.Spider):
    name = "holiday_stationstores"
    item_attributes = {"brand": "Holiday Stationstores", "brand_wikidata": "Q5880490"}
    allowed_domains = ["www.holidaystationstores.com"]
    download_delay = 0.2

    def start_requests(self):
        yield scrapy.Request(
            "https://www.holidaystationstores.com/Locations/GetAllStores",
            method="POST",
            callback=self.parse_all_stores,
        )

    def parse_all_stores(self, response):
        all_stores = json.loads(response.text)

        for store_id, store in all_stores.items():
            # GET requests get blocked by their Incapsula bot protection, but POST works fine
            yield scrapy.Request(
                f"https://www.holidaystationstores.com/Locations/Detail?storeNumber={store_id}",
                method="POST",
                meta={"store": store},
            )

    def parse(self, response):
        store = response.meta["store"]

        address = (
            response.xpath('//div[@class="col-lg-4 col-sm-12"]/text()')[1]
            .extract()
            .strip()
        )
        city_state = (
            response.xpath('//div[@class="col-lg-4 col-sm-12"]/text()')[2]
            .extract()
            .strip()
        )
        city, state = city_state.split(", ")
        phone = (
            response.xpath('//div[@class="HolidayFontColorRed"]/text()')
            .extract_first()
            .strip()
        )
        services = "|".join(
            response.xpath(
                '//ul[@style="list-style-type: none; padding-left: 1.0em; font-size: 12px;"]/li/text()'
            ).extract()
        ).lower()
        open_24_hours = (
            "24 hours" in response.css(".body-content .col-lg-4").get().lower()
        )

        properties = {
            "name": f"Holiday #{store['Name']}",
            "lon": store["Lng"],
            "lat": store["Lat"],
            "addr_full": address,
            "phone": phone,
            "ref": store["ID"],
            "city": city.strip(),
            "state": state.strip(),
            "website": response.url,
            "opening_hours": "24/7" if open_24_hours else self.opening_hours(response),
            "extras": {
                "amenity:fuel": True,
                "fuel:diesel": "diesel" in services or None,
                "atm": "atm" in services or None,
                "fuel:e85": "e85" in services or None,
                "hgv": "truck" in services or None,
                "fuel:propane": "propane" in services or None,
                "car_wash": "car wash" in services or None,
                "fuel:cng": "cng" in services or None,
            },
        }

        yield GeojsonPointItem(**properties)

    def opening_hours(self, response):
        hour_part_elems = response.xpath(
            '//div[@class="row"][@style="font-size: 12px;"]'
        )
        day_groups = []
        this_day_group = None

        if hour_part_elems:
            for hour_part_elem in hour_part_elems:
                day = hour_part_elem.xpath(
                    './/div[@class="col-3"]/text()'
                ).extract_first()
                hours = hour_part_elem.xpath(
                    './/div[@class="col-9"]/text()'
                ).extract_first()

                if not hours or hours.lower() == "closed":
                    continue

                day = day[:2]
                match = re.search(
                    r"^(\d{1,2}):(\d{2})\s*(a|p)m - (\d{1,2}):(\d{2})\s*(a|p)m?$",
                    hours.lower(),
                )
                (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

                f_hr = int(f_hr)
                if f_ampm == "p":
                    f_hr += 12
                elif f_ampm == "a" and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm == "p":
                    t_hr += 12
                elif t_ampm == "a" and t_hr == 12:
                    t_hr = 0

                hours = "{:02d}:{}-{:02d}:{}".format(
                    f_hr,
                    f_min,
                    t_hr,
                    t_min,
                )

                if not this_day_group:
                    this_day_group = {"from_day": day, "to_day": day, "hours": hours}
                elif this_day_group["hours"] != hours:
                    day_groups.append(this_day_group)
                    this_day_group = {"from_day": day, "to_day": day, "hours": hours}
                elif this_day_group["hours"] == hours:
                    this_day_group["to_day"] = day

            if this_day_group:
                day_groups.append(this_day_group)

        hour_part_elems = response.xpath(
            '//span[@style="font-size:90%"]/text()'
        ).extract()
        if hour_part_elems:
            day_groups.append(
                {"from_day": "Mo", "to_day": "Su", "hours": "00:00-23:59"}
            )

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours
