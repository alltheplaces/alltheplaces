# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonalsSISpider(scrapy.Spider):

    name = "mcdonalds_si"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.si"]
    start_urls = ("https://www.mcdonalds.si/restavracije/",)

    def parse_hour(self, time_str):
        sh = sm = eh = em = ""
        match = re.search(
            r"([0-9]{1,2}):([0-9]{1,2}) - ([0-9]{1,2}):([0-9]{1,2})", time_str
        )
        if match:
            sh, sm, eh, em = match.groups()

        return "%02d:%02d-%02d:%02d" % (
            int(sh),
            int(sm),
            int(eh) + 12 if int(eh) < 13 else int(eh),
            int(em),
        )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        data = data.xpath("//tr")
        index = 0
        for item in data:
            if index == 7:
                break
            day_hour = item.xpath("td[2]/text()").extract_first()

            short_day = weekdays[index]
            hours = self.parse_hour(day_hour)
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
        if len(day_groups) == 1 and not day_groups[0]:
            return None
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

    def parse_data(self, data):
        name = address = phone = lat = lon = ""
        data = data.xpath('//div[@id="map"]')
        name = data.xpath("//@data-title").extract_first()
        address = data.xpath("//@data-address").extract_first()
        phone = data.xpath("//@data-tel").extract_first()
        lat = data.xpath("//@data-map-x").extract_first()
        lon = data.xpath("//@data-map-y").extract_first()
        return name, address, phone, lat, lon

    def parse_store(self, response):
        name, address, phone, lat, lon = self.parse_data(response)
        properties = {
            "ref": response.meta["ref"],
            "phone": phone,
            "lon": lon,
            "lat": lat,
            "name": name,
            "addr_full": address,
        }

        opening_hours = self.store_hours(response)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        index = 0
        stores = response.xpath('//div[@class="header-block"]/h2/a/@href').extract()
        for store in stores:
            index = index + 1
            yield scrapy.Request(
                "https://www.mcdonalds.si" + store,
                meta={"ref": index},
                callback=self.parse_store,
            )
