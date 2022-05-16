# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class HomeBargainsUkSpider(scrapy.Spider):
    name = "home_bargains_uk"
    item_attributes = {"brand": "Home Bargains", "brand_wikidata": "Q5888229"}
    allowed_domains = ["homebargains.co.uk"]
    start_urls = [
        "https://storelocator.homebargains.co.uk/all-stores",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        remove_dupes_hrefs = []

        all_hrefs = response.xpath('//*[@class="store"]//@href').extract()

        [remove_dupes_hrefs.append(x) for x in all_hrefs if x not in remove_dupes_hrefs]

        for href in remove_dupes_hrefs:
            yield scrapy.Request(response.urljoin(href), callback=self.parse_store)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            d, h = hour.split()
            day = d.capitalize()
            open_time, close_time = h.split("-")

            if open_time == "closed":
                pass
            else:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        full_address = response.xpath('//*[@itemprop="address"]/text()').extract()
        addr = full_address[:-1]
        addr = ",".join(addr).strip()

        properties = {
            "ref": re.search(r"store\/(.*)\/", response.url).group(1),
            "name": response.xpath("//h1/text()").extract_first().strip(),
            "addr_full": addr,
            "country": "United Kingdom",
            "lat": response.xpath('//*[@itemprop="latitude"]/text()').extract_first(),
            "lon": response.xpath('//*[@itemprop="longitude"]/text()').extract_first(),
            "phone": response.xpath(
                '//*[@class="telephone print-only"]/text()'
            ).extract_first(),
            "website": response.url,
        }

        hours = self.parse_hours(
            response.xpath('//*[@itemprop="openingHours"]/@datetime').extract()
        )
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
