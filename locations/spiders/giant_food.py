import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class GiantFoodSpider(scrapy.Spider):
    name = "giant_food"
    item_attributes = {"brand": "Giant Food", "brand_wikidata": "Q5558336"}
    allowed_domains = ["giantfood.com"]

    start_urls = ("https://stores.giantfood.com/",)

    def parse(self, response):
        urls = response.xpath('//a[contains(@class, "DirectoryList-itemLink")]/@href').extract()
        if urls:  # state or city list
            for url in urls:
                if len(url.split("/")) == 3:  # straight to store page
                    yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
                else:
                    yield scrapy.Request(response.urljoin(url))
        else:  # store list
            urls = response.xpath('//a[contains(@class, "Teaser-titleLink")]/@href').extract()
            for url in urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        store_number = (
            response.xpath('//div[contains(@class, "StoreDetails-storeNum")]/text()').extract()[-1].strip("#")
        )
        properties = {
            "ref": store_number,
            "name": response.xpath('//meta[@itemprop="name"]/@content').extract_first(),
            "street_address": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]//text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            "country": response.xpath('normalize-space(//span[@itemprop="address"]/@data-country)').extract_first(),
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }

        hours = self.parse_hours(
            response.xpath('//div[contains(@class, "StoreDetails")]//tr[@itemprop="openingHours"]/@content').extract()
        )
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            if "All Day" in hour:
                day = hour.split(" ")[0]
                open_time = "12:00"
                close_time = "23:59"
            else:
                day, open_time, close_time = re.search(
                    r"([a-z]{2})\s([0-9:]+)-([0-9:]+)", hour, flags=re.IGNORECASE
                ).groups()
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)
        return opening_hours.as_opening_hours()
