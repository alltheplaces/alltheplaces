# -*- coding: utf-8 -*-
import scrapy
import unicodedata
import re
from locations.items import GeojsonPointItem

regex = r"(^\D)"
regex_time = r"(1[0-2]|0[1-9]|[1-9]):[0-5]\d\s?[AaPp][Mm]"
regex_am = r"\s?([Aa][Mm])"
regex_pm = r"\s?([Pp][Mm])"


class MonicalsSpider(scrapy.Spider):
    name = "monicals_pizza"
    item_attributes = {"brand": "Monical's Pizza", "brand_wikidata": "Q6900121"}
    allowed_domains = ["www.monicals.com"]
    start_urls = ["http://www.monicals.com/locations/"]

    def parse(self, response):
        stores = response.xpath('//*[@itemprop="name"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(store, callback=self.parse_store)

    def convert_hours(self, hour):
        for i in range(len(hour)):
            cleaned_times = ""
            if re.match(regex_time, hour[i]):
                if " – " in hour[i]:
                    hours_to = hour[i].split(" – ")
                    for ampm in hours_to:
                        if re.search(regex_pm, ampm):
                            ampm = re.sub(regex_pm, "", ampm)
                            hour_min = ampm.split(":")
                            if int(hour_min[0]) < 12:
                                hour_min[0] = str(12 + int(hour_min[0]))
                                cleaned_times += ":".join(hour_min)

                        if re.search(regex_am, ampm):
                            ampm = re.sub(regex_am, "", ampm)
                            hour_min = ampm.split(":")
                            if len(hour_min[0]) < 2:
                                hour_min[0] = hour_min[0].zfill(2)
                                cleaned_times += (":".join(hour_min)) + "-"
                            else:
                                cleaned_times += (":".join(hour_min)) + "-"
                else:
                    cleaned_times += "Special Hours"
            else:
                cleaned_times += "Closed"
            hour[i] = cleaned_times
        return hour

    def convert_days(self, days):
        days = [x for x in days if x]
        for i in range(len(days)):
            days[i] = unicodedata.normalize("NFKD", days[i])
            days[i] = days[i].strip()
            if days[i]:
                if re.match(regex, days[i]):
                    if "day" and "–" in days[i]:
                        day_from = days[i][:2]
                        try:  # Fix for the Chillicolthe store
                            day_to = days[i].split(" – ")[1][:2]
                            days[i] = day_from + "-" + day_to
                        except:
                            days[i] = day_from + "-" + "Sa"
                    elif "day" and "&" in days[i]:
                        day_from = days[i][:2]
                        day_to = days[i].split(" & ")[1][:2]
                        days[i] = day_from + "-" + day_to
                    else:
                        days[i] = days[i][:2]
                else:
                    days[i] = ""
        days = [x for x in days if x]
        return days

    def parse_store(self, response):
        lat = response.xpath('//*[@id="location-lat"]/@value').extract_first()

        lon = response.xpath('//*[@id="location-lng"]/@value').extract_first()

        name = response.xpath('//div[@class="title-wrap"]/h2/text()').extract_first()

        phone = response.xpath('//div[@class="title-wrap"]/div/text()').extract_first()

        street = (
            response.xpath('//li[@itemprop="streetAddress"]/text()')
            .extract_first()
            .strip()
        )

        city = response.xpath(
            '//span[@itemprop="addressLocality"]/text()'
        ).extract_first()

        state = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract_first()

        postcode = response.xpath(
            '//span[@itemprop="postalCode"]/text()'
        ).extract_first()

        website = response.xpath('//*[@id="my_location_url"]/@value').extract_first()

        address = "{}{} {} {}".format(street, city, state, postcode)

        # Some pages post notices such as "No longer accepting checks"
        # in the day/hours open section
        hour = response.xpath(
            '//*[@class="location-sidebar-item"][2]/descendant::*[contains('
            '., "am") or contains(., "pm") or contains('
            '., "Closed")]/text()'
        ).extract()

        day = self.convert_days(
            response.xpath(
                '//*[@class="location-sidebar-item"][2]/descendant::*[contains('
                '., "Sunday") or contains(., "Monday") or contains('
                '., "Tuesday") or contains(., "Wednesday") or contains('
                '., "Thursday") or contains(., "Friday") or contains('
                '., "Saturday")]/text()'
            ).extract()
        )

        for i in range(len(hour)):
            hour[i] = unicodedata.normalize("NFKD", hour[i])  # handle \xa0
            hour[i] = hour[i].strip()
        hour = [x for x in hour if x]
        hour = self.convert_hours(hour)

        opening_hours = ", ".join("{} : {}".format(*t) for t in zip(day, hour))

        yield GeojsonPointItem(
            lat=lat,
            lon=lon,
            addr_full=address,
            street=street,
            city=city,
            state=state,
            postcode=postcode,
            phone=phone,
            website=website,
            opening_hours=opening_hours,
            ref=response.url,
        )
