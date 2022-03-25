# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ApplebeesSpider(scrapy.Spider):
    name = "applebees"
    item_attributes = {"brand": "Applebees", "brand_wikidata": "Q621532"}
    allowed_domains = ["restaurants.applebees.com"]
    start_urls = ("https://restaurants.applebees.com/en-us/",)

    def parse(self, response):
        for url in response.xpath('//*[@id="bowse-content"]//@href').extract():
            yield scrapy.Request(url, callback=self.parse_state)

    def parse_state(self, response):
        for url in response.xpath('//*[@class="map-list"]//@href').extract():
            yield scrapy.Request(url, callback=self.parse_city)

    def parse_city(self, response):
        for url in response.xpath(
            '//*[@class="map-list-item-header"]/a[@class="ga-link"]/@href'
        ).extract():
            yield scrapy.Request(url, callback=self.parse_store)

    def store_hours(self, store_hours):
        o = OpeningHours()

        day_groups = []
        this_day_group = None
        for line in store_hours:
            # Applebees always seems to have a single dow
            # in each opening hours object
            day = line["dayOfWeek"][0][:2]

            if not line["opens"]:
                continue

            match = re.search(r"^(\d{1,2}):(\d{2})\D*?([APap])[Mm]$", line["opens"])
            (f_hr, f_min, f_ampm) = match.groups()
            match = re.search(r"^(\d{1,2}):(\d{2})\D*?([APap])[Mm]$", line["closes"])
            (t_hr, t_min, t_ampm) = match.groups()

            f_hr = int(f_hr)
            if f_ampm.lower() == "p":
                f_hr += 12
            elif f_ampm.lower() == "a" and f_hr == 12:
                f_hr = 0
            t_hr = int(t_hr)
            if t_ampm.lower() == "p":
                t_hr += 12
            elif t_ampm.lower() == "a" and t_hr == 12:
                t_hr = 0

            hours = "{:02d}:{}-{:02d}:{}".format(f_hr, f_min, t_hr, t_min)

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        if this_day_group:
            day_groups.append(this_day_group)

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
                elif day_group["from_day"] == "Mo" and day_group["to_day"] == "Su":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse_store(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )

        if not data or isinstance(data, dict):
            return

        data = data[0]

        o = OpeningHours()
        for h in response.xpath('//span[@class="daypart"]'):
            d = h.xpath("@data-daypart").extract_first()[:2]
            open_time = h.xpath('//span[@class="time-open"]/text()').extract_first()
            close_time = h.xpath('//span[@class="time-close"]/text()').extract_first()
            if open_time and close_time:
                o.add_range(d, open_time, close_time, "%I:%M%p")

        yield GeojsonPointItem(
            lat=float(data["geo"]["latitude"]),
            lon=float(data["geo"]["longitude"]),
            website=response.xpath(
                '//head/link[@rel="canonical"]/@href'
            ).extract_first(),
            ref=response.xpath('//head/link[@rel="canonical"]/@href').extract_first(),
            opening_hours=o.as_opening_hours(),
            addr_full=data.get("address", {}).get("streetAddress"),
            city=data.get("address", {}).get("addressLocality"),
            state=data.get("address", {}).get("addressRegion"),
            postcode=data.get("address", {}).get("postalCode"),
            country=data.get("address", {}).get("addressCountry"),
            phone=data.get("address", {}).get("telephone"),
        )
