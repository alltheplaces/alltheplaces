# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class StHubertSpider(scrapy.Spider):
    name = "st_hubert"
    item_attributes = {"brand": "St Hubert"}
    allowed_domains = ["st-hubert.com"]
    start_urls = ["http://www.st-hubert.com/salle-manger/rotisserie/recherche.en.html"]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            times = hour.split(" ")
            day = times[0]
            open_time, close_time = times[1].split("-")
            if close_time == "24:00":
                close_time = "00:00"

            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        coords = response.xpath(
            '//*[@class="itinerary btn-default-plain big"]/@href'
        ).extract_first()
        coords = re.search(r"@(.*?)\?", coords).groups()[0]
        lat, lng = coords.split(",")
        lng = lng[1:]

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.en.html|$)", response.url).group(1),
            "name": response.xpath(
                '//*[@class="main page-local"]/h1/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                '//*[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//*[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//*[@itemprop="addressRegion"]/@content'
            ).extract_first(),
            "postcode": response.xpath(
                '//*[@itemprop="postalCode"]/@content'
            ).extract_first(),
            "country": "CA",
            "lat": lat,
            "lon": lng,
            "phone": response.xpath(
                '//*[@itemprop="telephone"]/@content'
            ).extract_first(),
            "website": response.url,
        }

        try:
            h = self.parse_hours(
                response.xpath('//*[@itemprop="openingHours"]/@content').extract()
            )

            if h:
                properties["opening_hours"] = h
        except:
            pass

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//*[@class="content_options"]/div/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)
