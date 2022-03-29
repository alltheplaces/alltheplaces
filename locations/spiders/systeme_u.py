# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SystemeUSpider(scrapy.Spider):
    name = "systeme_u"
    item_attributes = {"brand": "Systeme U"}
    allowed_domains = ["magasins-u.com"]
    start_urls = [
        "https://www.magasins-u.com/sitemap.xml",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        days = hours[0].split(",")

        for d in days:
            times = d.split(" ")
            day = times[0]
            if times[1] == "Fermé":
                pass
            else:
                open_time, close_time = times[1].split("-")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('//*[@id="libelle-magasin"]/text()').extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//*[@itemprop="streetAddress"]/text())'
            ).extract_first(),
            "city": response.xpath(
                '//*[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//*[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "country": "FR",
            "lat": response.xpath('//*[@id="map-magasin"]/@data-lat').extract_first(),
            "lon": response.xpath('//*[@id="map-magasin"]/@data-lng').extract_first(),
            "phone": response.xpath(
                '//*[@itemprop="telephone"]/text()'
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
        xml = scrapy.selector.Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            try:
                type = re.search(r"com\/(.*?)\/", url).group(1)
                if type == "magasin":
                    yield scrapy.Request(url, callback=self.parse_stores)
            except:
                pass
