# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import date


from locations.items import GeojsonPointItem


class AthletaSpider(scrapy.Spider):
    name = "athleta"
    item_attributes = {"brand": "Athleta"}
    allowed_domains = ["stores.athleta.net"]
    athleta_url = "http://stores.athleta.net"
    start_urls = (athleta_url,)

    def store_hours(self, store_hours):
        if store_hours is None:
            return ""
        day_groups = []
        this_day_group = None
        for line in store_hours:
            if "closed" in line:
                match = re.search(r"^([A-z]{1,2}) ([A-z]*):-:$", line)
                (day, closed) = match.groups()
                hours = closed
            else:
                match = re.search(
                    r"^([A-z]{1,2}) (\d{1,2})[:]?(\d{1,2})-(\d{1,2})[:]?(\d{1,2})$",
                    line,
                )
                (day, f_hr, f_min, t_hr, t_min) = match.groups()

                f_hr = int(f_hr)
                t_hr = int(t_hr)
                try:
                    f_min = int(f_min)
                except ValueError:
                    f_min = 0
                try:
                    t_min = int(t_min)
                except ValueError:
                    t_min = 0

                hours = "{:02d}:{:02d}-{:02d}:{:02d}".format(f_hr, f_min, t_hr, t_min)

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

    def parse(self, response):
        data = response.xpath(
            '//div[@class="cities"]/div[@class="subLocation"]/a/@href'
        ).extract()
        for store in data:
            yield scrapy.Request(self.athleta_url + store, callback=self.parse_store)

    def parse_store(self, response):
        store_data = response.xpath('//div[@id="content-sidebar-wrap"]')
        name = (
            store_data.xpath('.//div[@class="entry-content"]/h1/text()')
            .extract()[0]
            .split(" in ", 1)[0]
        )
        store_details = store_data.xpath(
            './/div[@id="widget_Athleta_Stores_Details_div"]'
        )
        address = store_details.xpath(".//address/span[@itemprop]/text()").extract()
        (num, street) = (address[0], address[0])
        if " " in address[0]:
            (num, street) = address[0].split(" ", 1)
        addr1 = address.pop(0).strip()
        if len(address) > 5:
            addr1 += ", " + address.pop(0).strip()
        city = address.pop(0)
        state = address.pop(0)
        zip_code = address.pop(0)
        country = address.pop(0)
        phone = ""
        if len(address):
            phone = address.pop(0)
        properties = {
            "phone": phone,
            "ref": response.url.split("store-")[1].rstrip("/"),
            "name": name,
            "opening_hours": self.store_hours(
                store_details.xpath(
                    './/time[@itemprop="openingHours"]/@datetime'
                ).extract()
            ),
            "addr_full": addr1,
            "housenumber": num,
            "street": street,
            "city": city,
            "state": state,
            "postcode": zip_code,
            "country": country,
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
