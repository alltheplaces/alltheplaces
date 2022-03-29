# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonaldsLUSpider(scrapy.Spider):

    name = "mcdonalds_lu"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.lu"]
    start_urls = ("http://www.mcdonalds.lu/",)

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        day_hours = data.xpath('.//div[@class="zeiten_zeit"]//text()').extract()

        index = 0
        for day_hour in day_hours:
            if index == 7:
                break

            hours = ""
            match = re.search(
                r"([0-9]{1,2}):([0-9]{1,2}) - ([0-9]{1,2}):([0-9]{1,2}) ", day_hour
            )
            if not match:
                return None
            sh, sm, eh, em = match.groups()
            short_day = weekdays[index]
            hours = "{}:{}-{}:{}".format(
                sh, sm, int(eh) + 12 if int(eh) < 12 else int(eh), em
            )
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
        data = response.text

        name = self.parse_name(data)
        address = self.parse_address(data)
        phone = self.parse_phone(data)
        lat, lon = self.parse_latlon(data)
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
        matches = re.finditer(r"<a id=\"snav_(1.*)\">", response.text)
        for matchNum, match in enumerate(matches):
            ref = match.groups()[0]
            yield scrapy.Request(
                "http://www.mcdonalds.lu/content.php?r=" + ref + "&lang=de",
                meta={"ref": ref},
                callback=self.parse_store,
            )
