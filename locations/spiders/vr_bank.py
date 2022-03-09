import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Montag": "Mo",
    "Dienstag": "Tu",
    "Mittwoch": "We",
    "Donnerstag": "Th",
    "Freitag": "Fr",
    "Samstag": "Sa",
    "Sonntag": "Su",
}


class VRBankSpider(scrapy.Spider):
    name = "vr_bank"
    allowed_domains = ["www.vr.de"]
    start_urls = ["https://www.vr.de/service/filialen-a-z/a.html"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) "
        "AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 "
        "Mobile/9B179 Safari/7534.48.3",
    }

    def process_hours(self, store_hours):
        opening_hours = OpeningHours()

        day = time = open_time = close_time = ""

        if store_hours is None:
            return

        for hour in store_hours:
            hour = hour.replace(": ", "#")
            try:
                day, time = hour.split("#")
            except ValueError:
                continue

            if time and day in DAY_MAPPING.keys():
                time = time.replace("24:00", "00:00")
                tms = []
                if "und" in time:
                    tms = [tm.strip() for tm in time.split("und")]
                else:
                    tms.append(time)

                for tm in tms:
                    try:
                        open_time, close_time = [
                            t.strip() for t in tm.replace("Uhr", "").strip().split("-")
                        ]

                        if open_time and close_time and day:
                            opening_hours.add_range(
                                day=DAY_MAPPING[day],
                                open_time=open_time,
                                close_time=close_time,
                                time_format="%H:%M",
                            )
                        else:
                            continue
                    except ValueError:
                        continue

        return opening_hours.as_opening_hours()

    def parse_details(self, response):
        name = street = zip = city = phone = website = latitude = longitude = ""

        name = response.xpath('//h1[@itemprop="name"]/text()').get()
        street = response.xpath('//span[@itemprop="streetAddress"]/text()').get()
        zip = response.xpath('//span[@itemprop="postalCode"]/text()').get()
        city = response.xpath('//span[@itemprop="addressLocality"]/text()').get()
        phone = response.xpath('//li[@itemprop="telephone"]/a/span/text()').get()
        website = response.xpath('//li[@itemprop="url"]/a/span/text()').get()

        m = re.search(r"lat&quot;:([-+]?[0-9]*\.?[0-9]*)", response.text)
        if m:
            latitude = m.group(1)

        m = re.search(r"lng&quot;:([-+]?[0-9]*\.?[0-9]*)", response.text)
        if m:
            longitude = m.group(1)

        hours = response.xpath(
            '//p[@itemprop="openingHoursSpecification"]/text()'
        ).getall()

        properties = {
            "ref": response.request.url,
            "name": name,
            "city": city,
            "street": street,
            "postcode": zip,
            "phone": phone,
            "website": website,
            "lat": latitude,
            "lon": longitude,
        }

        if hours:
            properties["opening_hours"] = self.process_hours(hours)

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        index = response.xpath(
            '//div[has-class("module module-linklist ym-clearfix")]/ul/li/a/@href'
        ).getall()

        for page in index:
            yield scrapy.Request(
                url=page,
                callback=self.parse_links,
            )

    def parse_links(self, response):
        list = response.xpath(
            '//div[has-class("module module-teaserlist ym-clearfix")]/div/a/@href'
        ).getall()
        for item in list:
            yield scrapy.Request(
                url=item,
                callback=self.parse_details,
            )
