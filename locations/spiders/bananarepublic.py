# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import date


from locations.items import GeojsonPointItem


class BananaRepublicSpider(scrapy.Spider):
    name = "bananarepublic"
    item_attributes = {"brand": "Banana Republic"}
    allowed_domains = ["bananarepublic.gap.com"]
    bananarepublic_url = "http://www.bananarepublic.com/products/store-locations.jsp"
    store_url = (
        "http://bananarepublic.gap.com/resources/storeLocations/v1/us/store/?storeid={}"
    )
    start_urls = (bananarepublic_url,)

    def store_hours(self, store_hours):
        if store_hours is None:
            return ""
        day_groups = []
        this_day_group = None
        for line in store_hours:
            if "CLOSED" in line:
                match = re.search(r"^([A-z]{1,3}): ([A-z]*)$", line)
                (day, closed) = match.groups()
                hours = closed
            else:
                match = re.search(
                    r"^([A-z]{1,3}): (\d{1,2})[:]?(\d{1,2})? (A|P)M - (\d{1,2})[:]?(\d{1,2})? (A|P)M$",
                    line,
                )
                (day, f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

                f_hr = int(f_hr)
                if f_ampm in ["p", "P"]:
                    f_hr += 12
                elif f_ampm in ["a", "A"] and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm in ["p", "P"]:
                    t_hr += 12
                elif t_ampm in ["a", "A"] and t_hr == 12:
                    t_hr = 0
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
        data = response.xpath('//div[@id="sdStoreStates"]//li/a/@href').extract()
        for store in data:
            match = re.search(r"^.+(-store)\-(\d{1,4})(.jsp)$", store)
            (_, store_id, _) = match.groups()
            yield scrapy.Request(
                self.store_url.format(store_id), callback=self.parse_store
            )

    def parse_store(self, response):
        store = response.json()["storeLocations"]["storeLocationList"]
        store_addr = store["storeAddress"]
        addr1 = store_addr["addressLine1"]
        (num, street) = (addr1, addr1)
        if " " in addr1:
            (num, street) = addr1.split(" ", 1)
        zip_code = store_addr["postalCode"]
        properties = {
            "phone": store_addr["phoneNumber"],
            "ref": store["storeId"],
            "name": store["storeName"],
            "opening_hours": self.store_hours(store.get("storeHours", None)),
            "lat": store["latitude"],
            "lon": store["longitude"],
            "addr_full": store_addr["addressLine1"],
            "housenumber": num,
            "street": street,
            "city": store_addr["cityName"],
            "state": store_addr["stateProvinceCode"],
            "postcode": zip_code,
            "country": store_addr["countryCode"],
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
