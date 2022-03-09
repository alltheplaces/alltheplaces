# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class CheckersSpider(scrapy.Spider):
    name = "checkers"
    item_attributes = {"brand": "Checkers Drive-In"}
    allowed_domains = ["checkers.com"]
    start_urls = ("https://www.checkers.com/locations/?zip_code=97035&radius=25000",)
    addr2regex = re.compile(r"^([A-Za-z\ \.]+)\, ([A-Z]+) ([0-9]+)$")
    dayMap = {
        "Mon": "Mo",
        "Tue": "Tu",
        "Wed": "We",
        "Thu": "Th",
        "Fri": "Fr",
        "Sat": "Sa",
        "Sun": "Su",
    }

    def opening_hours(self, location):
        days_hours_unp = location.xpath(
            './/table[@class="store-hours"]/tr/td/descendant-or-self::*/text()'
        ).extract()
        if not days_hours_unp:
            return None
        day_groups = []
        days_hours = []
        this_day_group = None
        for i in range(len(days_hours_unp)):
            if days_hours_unp[i] in self.dayMap:
                days_hours.append(
                    [
                        self.dayMap[days_hours_unp[i]],
                        days_hours_unp[i + 1] + " - " + days_hours_unp[i + 3],
                    ]
                )

        for day_hours in days_hours:
            day = day_hours[0]
            hours = day_hours[1]
            match = re.search(
                r"^(\d{1,2}):(\d{2})\w* (a|p)m - (\d{1,2}):(\d{2})\w* (a|p)m?$", hours
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

    def parse(self, response):
        id_to_loc = {}
        loc_re = r"lat: ([\-0-9\.]+), lng: ([\-0-9\.]+)};\r\n.*marker(\d+) = "
        loc_javascript = response.xpath("//script/text()")[-5].extract()
        locations = re.findall(loc_re, loc_javascript)
        for lat, lon, store_id in locations:
            id_to_loc[store_id] = {"lat": float(lat), "lon": float(lon)}

        for location in response.xpath('//li[@class="location-item "]'):
            addr_full = location.xpath(
                './/h2[@class="add-line-one"]/text()'
            ).extract_first()
            addr2 = location.xpath(
                './/h3[@class="add-line-two"]/text()'
            ).extract_first()
            city, state, zipcode = None, None, None
            if addr2:
                addr2 = addr2.strip()
                three_pieces = self.addr2regex.search(addr2)
                if three_pieces:
                    city, state, zipcode = three_pieces.groups()

            location_id = location.xpath("@id").extract_first()
            phone = location.xpath(
                './/i[@class="fa fa-phone"]/../strong/a/text()'
            ).extract_first()
            website = location.xpath(
                './/a[@class="view-location"]/@href'
            ).extract_first()

            unp = {
                "ref": location_id,
                "addr_full": addr_full,
                "website": website,
                "city": city,
                "state": state,
                "postcode": zipcode,
                "phone": phone,
            }

            opening_hours = self.opening_hours(location)
            if opening_hours:
                unp["opening_hours"] = opening_hours

            properties = {}
            for key in unp:
                if unp[key]:
                    properties[key] = unp[key]

            latlon = id_to_loc.get(location_id)
            if latlon:
                properties.update(latlon)

            yield GeojsonPointItem(**properties)
