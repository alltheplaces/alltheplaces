# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

DAYS = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class NextcareSpider(scrapy.Spider):
    name = "nextcare"
    item_attributes = {"brand": "NextCare Urgent Care"}
    allowed_domains = ["nextcare.com"]
    start_urls = ("https://nextcare.com/locations/",)

    def store_hours(self, hours):
        if not hours:
            return ""

        day_times = hours.split(",")
        normalize_day_times = []

        for day_time in day_times:
            day, hours = [x.strip() for x in day_time.split(": ")]
            normalize_hours = []

            if re.search("-", day):
                days = [x.strip() for x in day.split("-")]
                norm_days = "-".join([DAYS.get(x, "") for x in days])
            else:
                norm_days = DAYS.get(day, "")

            if re.search("Closed", hours):
                norm_hours = "off"
                normalize_hours.append(norm_hours)
            else:
                if re.search(" - ", hours):
                    hours = [x.strip() for x in hours.split(" - ")]
                    for hour in hours:
                        if hour[-2:] == "PM":
                            if re.search(":", hour[:-2]):
                                hora, minute = [x.strip() for x in hour[:-2].split(":")]
                                if int(hora) < 12:
                                    norm_hours = str(int(hora) + 12) + ":" + minute
                            else:
                                if int(hour[:-2]) < 12:
                                    norm_hours = str(int(hour[:-2]) + 12) + ":00"

                        elif hour[-2:] == "AM":
                            if re.search(":", hour[:-2]):
                                hora, minute = [x.strip() for x in hour[:-2].split(":")]
                                norm_hours = hora + ":" + minute
                            else:
                                norm_hours = hour[:-2] + ":00"
                        normalize_hours.append(norm_hours)
            normalize_day_times.append(" ".join([norm_days, "-".join(normalize_hours)]))
        return "; ".join(normalize_day_times)

    def parse(self, response):
        for location_url in response.xpath(
            '//div[@class="all_locs_address"]/a/@href'
        ).extract():
            yield scrapy.Request(
                location_url,
                callback=self.parse_location,
            )

    def parse_location(self, response):
        unp = {}  # Unprocessed properties
        properties = {}
        unp["phone"] = response.xpath(
            '//span[@itemprop="telephone"]/a/text()'
        ).extract_first()
        unp["name"] = response.xpath(
            '//span[@itemprop="name"]/h2[@class="loc_d_title"]/text()'
        ).extract_first()
        unp["ref"] = response.url
        unp["website"] = response.url

        addressdiv = response.xpath('//div[@itemprop="address"]')[0]
        unp["addr_full"] = addressdiv.xpath(
            './/span[@itemprop="streetAddress"]/text()'
        ).extract_first()
        unp["city"] = addressdiv.xpath(
            './/span[@itemprop="addressLocality"]/text()'
        ).extract_first()
        unp["state"] = addressdiv.xpath(
            './/span[@itemprop="addressRegion"]/text()'
        ).extract_first()
        unp["postcode"] = addressdiv.xpath(
            './/span[@itemprop="postalCode"]/text()'
        ).extract_first()

        uber_url = response.xpath(
            '//div[@class="heading-desktop"]/h5/a/@href'
        ).extract_first()
        latitude = uber_url.split("[latitude]=")[1]
        latitude = latitude.split("&dropoff")[0]
        longitude = uber_url.split("[longitude]=")[1]

        if latitude is not None and longitude is not None:
            unp["lat"] = latitude
            unp["lon"] = longitude

        hours = response.xpath('//ul[@class="loc_d_times row"]/li/text()').extract()
        opening_hours = None
        if hours:
            opening_hours = self.store_hours(",".join(hours))

        if opening_hours:
            properties["opening_hours"] = opening_hours

        for key in unp:
            if unp[key]:
                properties[key] = unp[key].strip()

        yield GeojsonPointItem(**properties)
