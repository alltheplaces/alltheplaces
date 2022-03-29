# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonaldsPTSpider(scrapy.Spider):

    name = "mcdonalds_pt"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["en.wikipedia.org", "www.mcdonalds.pt"]
    start_urls = ("https://en.wikipedia.org/wiki/List_of_postal_codes_in_Portugal",)

    def normalize_time(self, time_str, flag):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2}):[0-9]{1,2}", time_str)
        h, m = match.groups()

        if int(h) == 0:
            return "%02d:%02d" % (24, int(m))

        return "%02d:%02d" % (
            int(h) + 12 if flag and int(h) < 13 else int(h),
            int(m),
        )

    def store_hours(self, data):
        if not data:
            return None

        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        day_hours = data["periods"]
        for day_hour in day_hours:
            index = int(day_hour["day"])
            if index > 7:
                break
            hours = ""
            start = day_hour["open_hour"]
            end = day_hour["close_hour"]
            start = self.normalize_time(start, False)
            end = self.normalize_time(end, True)

            short_day = weekdays[index - 1]
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

    def parse_name(self, name):
        match = re.search(r"<h1>(.*)</h1>", name)
        return match.groups()[0].strip()

    def parse_latlon(self, data):
        match = re.search(r"sll=(.*),(.*)&amp;ss", data)
        return match.groups()[0].strip(), match.groups()[1].strip()

    def parse_phone(self, phone):
        match = re.search(r"Tel(.*)<br", phone)
        return match.groups()[0].strip()

    def parse_address(self, address):
        address = address[address.find("<h2>Adresse</h2>") + 16 : address.find("Tel")]
        match = re.sub("<[^<]+?>", "", address)
        return " ".join(match.split())

    def parse_store(self, response):
        stores = response.json()
        for store in stores:
            properties = {
                "ref": store["id"],
                "phone": store["phone"],
                "lat": store["coordinates"]["latitude"],
                "lon": store["coordinates"]["longitude"],
                "name": store["name"],
                "addr_full": store["address"],
                "city": store["city"],
                "postcode": store["postal_code"],
                "website": store["link"]["url"],
            }
            opening_hours = self.store_hours(store["opening_hours"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)

    def parse(self, response):
        postalCodes = response.xpath("//li/text()").extract()
        for postalCode in postalCodes:
            match = re.search(r"(\d{1,}) -", postalCode)
            if not match:
                continue
            postalCode = match.groups()[0]

            yield scrapy.Request(
                "https://www.mcdonalds.pt/web-api/Proxy/Restaurants?termo="
                + postalCode,
                callback=self.parse_store,
            )
