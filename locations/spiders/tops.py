import re

import scrapy

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature


class TopsSpider(scrapy.Spider):
    name = "tops"
    item_attributes = {"brand": "Tops", "brand_wikidata": "Q7825137", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.topsmarkets.com"]

    start_urls = ("http://www.topsmarkets.com/StoreLocator/Store_MapLocation_S.las?State=all",)

    def parse_address(self, data):
        filtered_data = []
        for item in data:
            if item.strip():
                filtered_data.append(item.strip())

        address = filtered_data[1]
        data = filtered_data[2]
        city = data.split(",")[0].strip()
        data = data.split(",")[1].strip()
        state = data.split(" ")[0]
        postal_code = data.split(" ")[1]

        return address, city, state, postal_code

    def parse_phone(self, data):
        filtered_data = []
        for item in data:
            if item.strip():
                filtered_data.append(item.strip())

        return filtered_data[1]

    def store_hours(self, store_hours):
        """This should capture these time formats as on website
                # Sunday 9:00 to 1:00PM, Mon-Fri 9:00AM to 8:00PM, Saturday 9:00AM to 5:00PM,
                # 24 Hours,
                # Sunday- Saturday, 6AM-11PM,
                # 6am - Midnight,
                # 6AM to Midnight,

        :param hours:
        :return:  string - in this format Mo-Th 11:00-12:00; Fr-Sa 11:00-01:00;
        """

        days = store_hours.split("<br>")
        days = days[:-1]
        m = []
        for day in days:
            d_split = day.split(": ")
            d_split[0] = DAYS_EN[d_split[0]]
            m.append((d_split[0], d_split[1]))
            # Now we have something like: ("Mo", "10AM-9PM")
            #                         OR: ("Mo", "10:30AM-9:30PM")

        day_groups = []
        this_day_group = dict()
        for day, hours_together in m:
            if hours_together == "CLOSED":
                continue

            hours_apart = hours_together.split("-")
            from_ = hours_apart[0]
            to_ = hours_apart[1]

            if ":" in from_:
                (from_h, from_m, from_ap) = re.findall("([0-9]{1,2}):([0-9]{1,2})([APM]{2})", from_)[0]
            else:
                (from_h, from_ap) = re.findall("([0-9]{1,2})([APM]{2})", from_)[0]
                from_m = "00"

            if ":" in to_:
                (to_h, to_m, to_ap) = re.findall("([0-9]{1,2}):([0-9]{1,2})([APM]{2})", to_)[0]
            else:
                (to_h, to_ap) = re.findall("([0-9]{1,2})([APM]{2})", to_)[0]
                to_m = "00"

            from_h = int(from_h)
            if from_ap == "PM" and (from_h != 12):
                from_h += 12

            to_h = int(to_h)
            if to_ap == "PM" and (to_h != 12):
                to_h += 12

            hours = "{:02}:{}-{:02}:{}".format(
                from_h,
                from_m,
                to_h,
                to_m,
            )

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

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
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse_store(self, response):
        data = response.xpath('//p[@class="Address"]//text()').extract()
        address, city, state, postal_code = self.parse_address(data)
        data = response.xpath('//p[@class="PhoneNumber"]//text()').extract()
        phone = self.parse_phone(data)
        properties = {
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": postal_code,
            "phone": phone,
            "ref": response.meta["ref"],
            "lon": response.meta["lon"],
            "lat": response.meta["lat"],
        }

        yield Feature(**properties)

    def parse(self, response):
        try:
            data = response.json()
        except ValueError:
            return
        for item in data:
            lat = item["Latitude"]
            lon = item["Longitude"]
            ref = item["StoreNbr"]

            yield scrapy.Request(
                "http://www.topsmarkets.com/StoreLocator/Store?L=" + item["StoreNbr"],
                meta={"lat": lat, "lon": lon, "ref": ref},
                callback=self.parse_store,
            )
