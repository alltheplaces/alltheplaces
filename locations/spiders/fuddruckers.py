# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

regex_am = r"\s?([Aa][Mm])"
regex_pm = r"\s?([Pp][Mm])"
base_url = "http://www.fuddruckers.com"


class FuddruckersSpider(scrapy.Spider):
    name = "fuddruckers"
    item_attributes = {"brand": "Fuddruckers", "brand_wikidata": "Q5507056"}
    allowed_domains = ["www.fuddruckers.com"]
    start_urls = [
        "http://www.fuddruckers.com/services/location/get_stores_by_position.php?lt=37.09024&lg=-95.712891&m=100&k=United+States",
    ]

    def convert_hours(self, hours):
        hours = [x.strip() for x in hours]
        hours = [x for x in hours if x]
        for i in range(len(hours)):
            converted_times = ""
            if hours[i] != "Closed":
                if hours[i] != "Open 24 Hours":
                    from_hr, to_hr = [hr.strip() for hr in hours[i].split("-")]
                    if re.search(regex_am, from_hr):
                        from_hr = re.sub(regex_am, "", from_hr)
                        hour_min = from_hr.split(":")
                        if len(hour_min[0]) < 2:
                            hour_min[0].zfill(2)
                        converted_times += (":".join(hour_min)) + "-"
                    else:
                        from_hr = re.sub(regex_pm, "", from_hr)
                        hour_min = from_hr.split(":")
                        if int(hour_min[0]) < 12:
                            hour_min[0] = str(12 + int(hour_min[0]))
                        converted_times += (":".join(hour_min)) + "-"

                    if re.search(regex_am, to_hr):
                        to_hr = re.sub(regex_am, "", to_hr)
                        hour_min = to_hr.split(":")
                        if len(hour_min[0]) < 2:
                            hour_min[0].zfill(2)
                        if int(hour_min[0]) == 12:
                            hour_min[0] = "00"
                        converted_times += ":".join(hour_min)
                    else:
                        to_hr = re.sub(regex_pm, "", to_hr)
                        hour_min = to_hr.split(":")
                        if int(hour_min[0]) < 12:
                            hour_min[0] = str(12 + int(hour_min[0]))
                        converted_times += ":".join(hour_min)
                else:
                    converted_times = "00:00-24:00"
            else:
                converted_times += "off"
            hours[i] = converted_times
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        hours = "".join("{} {} ".format(*t) for t in zip(days, hours))
        return hours

    def get_hours(self, response):
        hours = response.xpath(
            '//*[@id="store-profile"]/div[2]/div[2]/div[2]/div/table//tr/td[2]'
            "/text()"
        ).extract()
        hours = self.convert_hours(hours)
        yield scrapy.Request(
            self.start_urls[0], meta={"hours": hours}, callback=self.parse_stores
        )

    def parse(self, response):
        results = response.json()
        for i in results["places"]["positions"]["data"]:
            yield scrapy.Request(
                base_url + i["link"].strip("\\"), callback=self.get_hours
            )

    def parse_stores(self, response):
        results = response.json()
        hours = response.meta["hours"]
        for i in results["places"]["positions"]["data"]:
            yield GeojsonPointItem(
                opening_hours=hours,
                ref=i["id"],
                lat=float(i["lat"]),
                lon=float(i["lng"]),
                name=i["storename"],
                street=i["address"],
                city=i["city"],
                state=i["state"],
                postcode=i["zip"],
                country=i["country"],
                phone=i["phone"],
                website=base_url + i["link"].strip("\\"),
                addr_full="{} {}, {} {} {}".format(
                    i["address"], i["city"], i["state"], i["zip"], i["country"]
                ),
            )
