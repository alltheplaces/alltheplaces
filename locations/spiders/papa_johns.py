# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

day_map = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class PapaJohnsSpider(scrapy.Spider):
    name = "papa_johns"
    item_attributes = {"brand": "Papa John's Pizza", "brand_wikidata": "Q2759586"}
    allowed_domains = [
        "papajohns.com",
    ]

    start_urls = ("https://locations.papajohns.com/",)
    download_delay = 0.2

    def parse_hours(self, hours):
        if not hours:
            return ""
        try:
            opening_hours = OpeningHours()
            the_hours = json.loads(hours[0])
            for day in the_hours:
                the_day = day_map[day["day"]]
                the_start = str(day["intervals"][0]["start"])
                the_end = str(day["intervals"][0]["end"])
                if the_start == "0":
                    the_start = "000"
                if the_end == "0":
                    the_end = "000"
                opening_hours.add_range(
                    day=the_day,
                    open_time=the_start,
                    close_time=the_end,
                    time_format="%H%M",
                )
            return opening_hours.as_opening_hours()
        except IndexError:
            return ""

    def parse_store(self, response):
        hours = response.xpath(
            '//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days'
        ).extract()
        opening_hours = self.parse_hours(hours)

        if (
            response.xpath(
                '//address[@class="c-address"]/div[3]/span/text()'
            ).extract_first()
            is not None
        ):
            city = response.xpath(
                '//address[@class="c-address"]/div[3]/span/text()'
            ).extract_first()
        else:
            city = response.xpath(
                '//address[@class="c-address"]/div[2]/span/text()'
            ).extract_first()

        if (
            response.xpath(
                '//address[@class="c-address"]/div[2]/abbr/text()'
            ).extract_first()
            is not None
        ):
            the_state = response.xpath(
                '//address[@class="c-address"]/div[2]/abbr/text()'
            ).extract_first()
            the_postal = response.xpath(
                '//address[@class="c-address"]/div[2]/span[2]/text()'
            ).extract_first()
        else:
            the_state = response.xpath(
                '//address[@class="c-address"]/div[3]/abbr/text()'
            ).extract_first()
            the_postal = response.xpath(
                '//address[@class="c-address"]/div[3]/span[2]/text()'
            ).extract_first()

        if "/united-states/" in response.url:
            country = "US"
        elif "/canada/" in response.url:
            country = "CA"
        elif response.url == "https://locations.papajohns.com/index.html":
            return
        else:
            country = ""

        props = {
            "ref": response.xpath("//main/@itemid").extract_first().split("#")[1],
            "website": response.url,
            "addr_full": response.xpath(
                '//address[@class="c-address"]/div[1]/span/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@class="c-phone-number c-phone-main-number"]/a/text()'
            ).extract_first(),
            "city": city,
            "postcode": the_postal,
            "state": the_state,
            "opening_hours": opening_hours,
            "country": country,
            "lat": response.xpath(
                '//span[@class="coordinates"]/meta[1]/@content'
            ).extract_first(),
            "lon": response.xpath(
                '//span[@class="coordinates"]/meta[2]/@content'
            ).extract_first(),
        }

        yield GeojsonPointItem(**props)

    def parse_within_city(self, response):
        stores = response.xpath('//h2[@class="Teaser-title"]/a/@href').extract()

        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_store)

    def parse_city(self, response):
        cities = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        for city in cities:
            determine_multi_state = city.split("/")
            if len(determine_multi_state) == 4:
                yield scrapy.Request(
                    response.urljoin(city), callback=self.parse_within_city
                )
            else:
                yield scrapy.Request(response.urljoin(city), callback=self.parse_store)

    def parse_state(self, response):
        states = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        for state in states:
            determine_multi_state = state.split("/")
            if len(determine_multi_state) <= 5:
                yield scrapy.Request(response.urljoin(state), callback=self.parse_city)
            else:
                yield scrapy.Request(response.urljoin(state), callback=self.parse_store)

    def parse(self, response):
        countries = response.xpath(
            '//li[@class="Directory-listItem"]/a/@href'
        ).extract()

        for country in countries:
            yield scrapy.Request(response.urljoin(country), callback=self.parse_state)
