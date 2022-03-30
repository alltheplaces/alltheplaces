# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonaldsETSpider(scrapy.Spider):

    name = "mcdonalds_et"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.ee"]
    start_urls = ("http://www.mcdonalds.ee/et/restoranid",)

    def normalize_time(self, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2}) ([ap.m]{2})", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2}) ([ap.m]{2})", time_str)
            h, am_pm = match.groups()
            m = "0"
        else:
            h, m, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "p." else int(h),
            int(m),
        )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        day_hours = data.xpath('.//div[@class="opening-hours"]/div/p').extract()
        if len(day_hours) < 7:
            day_hours = data.xpath('.//div[@class="opening-hours"]/div/div/p').extract()
        index = 0
        for day_hour in day_hours:
            day_hour = day_hour.strip()
            hours = ""
            match = re.search(
                r"([0-9]{1,2}).([0-9]{1,2}) - ([0-9]{1,2}).([0-9]{1,2})", day_hour
            )
            if not match:
                continue
            else:
                sh, sm, eh, em = match.groups()
                hours = "{}:{}-{}:{}".format(
                    sh, sm, int(eh) + 12 if int(eh) < 12 else int(eh), em
                )
            short_day = weekdays[index]
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            index = index + 1

        day_groups.append(this_day_group)

        if not day_groups:
            return None

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
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse_latlon(self, response):
        match = re.search(r"q=(.*),(.*)&", response)
        lat, lon = match.groups()
        return lat, lon

    def parse_data(self, response):
        data = response.xpath('.//div[@class="field-content"]/text()').extract()
        return data[0], data[1].split(";")[0]

    def parse(self, response):
        stores = response.css(".open")
        for store in stores:
            ref = store.xpath('.//span[@class="number"]/text()').extract_first().strip()
            name = (
                store.xpath('.//div[@class="title"]/h4/text()').extract_first().strip()
            )
            lat, lon = self.parse_latlon(
                store.xpath('.//div[@class="col-info-lft"]/div/a/@href')
                .extract_first()
                .strip()
            )
            address, phone = self.parse_data(store)
            properties = {
                "ref": ref,
                "addr_full": address,
                "phone": phone,
                "name": name,
                "lat": lat,
                "lon": lon,
            }

            opening_hours = self.store_hours(store)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
