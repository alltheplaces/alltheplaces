# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonalsILSpider(scrapy.Spider):

    name = "mcdonalds_il"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["www.mcdonalds.co.il"]
    start_urls = (
        "https://www.mcdonalds.co.il/%D7%90%D7%99%D7%AA%D7%95%D7%A8_%D7%9E%D7%A1%D7%A2%D7%93%D7%94",
    )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Su", "Mo", "Th", "We", "Tu", "Fr", "Sa"]
        for day_hour in data:
            if day_hour["idx"] > 7:
                continue

            hours = ""
            start, end = (
                day_hour["value"].split("-")[0].strip(),
                day_hour["value"].split("-")[1].strip(),
            )

            short_day = weekdays[day_hour["idx"] - 1]
            hours = "{}:{}-{}:{}".format(start[:2], start[3:], end[:2], end[3:])
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

    def parse_Ref(self, data):
        match = re.search(r"store_id=(.*\d)", data)
        ref = match.groups()[0]
        return ref

    def parse_name(self, name):
        name = name.xpath("//h1/text()").extract_first()
        return name.strip()

    def parse_latlon(self, data):
        lat = lon = ""
        data = data.xpath('//div[@id="map"]')
        lat = data.xpath("//@data-lat").extract_first()
        lon = data.xpath("//@data-lng").extract_first()
        return lat, lon

    def parse_phone(self, phone):
        phone = phone.xpath(
            '//div[@class="padding_hf_v sp_padding_qt_v"]/a/text()'
        ).extract_first()
        if not phone:
            return ""
        return phone.strip()

    def parse_address(self, address):
        address = address.xpath("//h2/strong/text()").extract_first()
        return address.strip()

    def parse_store(self, response):
        data = response.text
        name = self.parse_name(response)
        address = self.parse_address(response)
        phone = self.parse_phone(response)
        lat, lon = self.parse_latlon(response)
        properties = {
            "ref": response.meta["ref"],
            "phone": phone,
            "lon": lon,
            "lat": lat,
            "name": name,
            "addr_full": address,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        stores = response.xpath('//div[@class="store_wrap link"]/a/@href').extract()
        for store in stores:
            ref = self.parse_Ref(store)
            yield scrapy.Request(
                "https:" + store, meta={"ref": ref}, callback=self.parse_store
            )
