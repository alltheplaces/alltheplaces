import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class ChipotleSpider(scrapy.Spider):
    name = "chipotle"
    item_attributes = {"brand": "Chipotle", "brand_wikidata": "Q465751"}
    allowed_domains = ["chipotle.com", "chipotle.ca", "chipotle.co.uk"]

    def start_requests(self):
        urls = [
            "https://locations.chipotle.com/",
            "https://locations.chipotle.ca/",
            "https://locations.chipotle.co.uk/london",
        ]

        for url in urls:
            if url == "https://locations.chipotle.co.uk/london":
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_same_city,
                    meta={"url": "https://locations.chipotle.co.uk/"},
                )
            else:
                yield scrapy.Request(url=url, callback=self.parse_state, meta={"url": url})

    def parse_state(self, response):
        states = response.xpath('//*[@class="Directory-listLink"]/@href').extract()
        count = response.xpath('//*[@class="Directory-listLink"]/@data-count').extract()

        base_url = response.meta.get("url")

        for c, state in zip(count, states):
            url = base_url + state
            if c == "(1)":
                yield scrapy.Request(url=url, callback=self.parse_store)
            elif state == "dc/washington" or state == "nd/fargo":
                yield scrapy.Request(url=url, callback=self.parse_same_city, meta={"url": base_url})
            else:
                yield scrapy.Request(url=url, callback=self.parse_city, meta={"url": base_url})

    def parse_city(self, response):
        city_count = response.xpath('//*[@class="Directory-listLink"]/@data-count').extract()
        cities = response.xpath('//*[@class="Directory-listLink"]/@href').extract()

        base_url = response.meta.get("url")

        for count, city in zip(city_count, cities):
            url = base_url + city
            if count == "(1)":
                yield scrapy.Request(url=url, callback=self.parse_store)
            else:
                yield scrapy.Request(url=url, callback=self.parse_same_city, meta={"url": base_url})

    def parse_same_city(self, response):
        stores = response.xpath('//*[@class="Teaser-titleLink"]/@href').extract()
        base_url = response.meta.get("url")

        for store in stores:
            if "london" in store:
                pass
            else:
                store = store[2:]
            url = base_url + store

            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = list(dict.fromkeys(hours))

        for hour in hours:
            hour = hour.split(" ")
            day = hour[0]
            open_time, close_time = hour[1].split("-")

            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            "ref": "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()),
            "name": response.xpath('//*[@itemprop="name"]/text()').extract_first().strip(),
            "street_address": response.xpath('//*[@class="c-address-street-1"]/text()').extract_first(),
            "city": response.xpath('//*[@class="c-address-city"]/text()').extract_first(),
            "state": response.xpath('//*[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//*[@itemprop="addressCountry"]/text()').extract_first(),
            "lat": response.xpath('//*[@itemprop="latitude"]/@content').extract_first(),
            "lon": response.xpath('//*[@itemprop="longitude"]/@content').extract_first(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').extract_first(),
            "website": response.url,
        }

        try:
            hours = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())

            if hours:
                properties["opening_hours"] = hours
        except:
            pass

        yield Feature(**properties)
