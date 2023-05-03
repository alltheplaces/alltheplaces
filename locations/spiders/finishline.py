import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class FinishlineSpider(scrapy.Spider):
    name = "finishline"
    item_attributes = {"brand": "Finish Line", "brand_wikidata": "Q5450341"}
    allowed_domains = ["stores.finishline.com"]
    download_delay = 0.5
    start_urls = ("https://stores.finishline.com/",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                day, open_time, close_time = re.search(r"([A-Za-z]{2})\s([\d:]+)-([\d:]+)", hour).groups()
            except:
                continue
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        ref = re.findall(r".com/(.+?)/(.+?)/(.+?).html", response.url)[0]
        ref = "_".join(ref)

        address_parts = response.xpath('//span[@itemprop="streetAddress"]/span/text()').extract()
        properties = {
            "street_address": " ".join([a.strip() for a in address_parts]),
            "name": response.xpath('//span[@class="location-name-geo"]/text()').extract_first(),
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            "state": response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
            "brand": response.xpath('//span[@class="location-name-brand"]/text()').extract_first().strip(),
        }

        hours = self.parse_hours(response.xpath('//tr[@itemprop="openingHours"]/@content').extract())

        if hours:
            properties["opening_hours"] = hours
        yield Feature(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@class="c-location-grid-item"]')
        for store in stores:
            url = store.xpath(
                './/div[@class="c-location-grid-links"]/div/a[contains(text(), "Store Details")]/@href'
            ).extract_first()
            if url:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)
            else:
                ref = re.findall(r".com/(.+?)/(.+?).html", response.url)[0]
                ref = "_".join(ref)
                name = store.xpath('.//span[@class="location-name-geo"]/text()').extract_first()
                address_parts = store.xpath('.//span[@class="c-address-street"]/span/text()').extract()
                brand = (
                    store.xpath('.//span[@class="location-name-brand"]/text()')
                    .extract_first()
                    .replace("  ", " ")
                    .strip()
                )
                properties = {
                    "street_address": " ".join([a.strip() for a in address_parts]),
                    "name": name,
                    "phone": store.xpath(
                        'normalize-space(.//span[contains(@class, "c-phone-main-number-span")]/text())'
                    ).extract_first(),
                    "city": store.xpath(
                        'normalize-space(.//span[@class="c-address-city"]/span/text())'
                    ).extract_first(),
                    "state": store.xpath('normalize-space(.//abbr[@class="c-address-state"]/text())').extract_first(),
                    "postcode": store.xpath('normalize-space(.//span[@class="c-address-postal-code"]/text())')
                    .extract_first()
                    .strip(),
                    "ref": "_".join([ref, brand, name]).replace(" ", "-").lower(),
                    "website": response.url,
                    "brand": brand,
                }
                hours = self.parse_hours(store.xpath('//tr[@itemprop="openingHours"]/@content').extract())
                if hours:
                    properties["opening_hours"] = hours
                yield Feature(**properties)

    def parse_state(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            path_split = len(path.split("/"))
            if path_split == 2:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            path_split = len(path.split("/"))
            if path_split == 1:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif path_split == 2:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
