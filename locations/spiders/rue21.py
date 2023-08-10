import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class Rue21Spider(scrapy.Spider):
    download_delay = 0.2
    name = "rue21"
    item_attributes = {"brand": "rue21", "brand_wikidata": "Q7377762"}
    allowed_domains = ["rue21.com"]
    start_urls = ("https://stores.rue21.com/index.html",)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        hours = elements.xpath('.//tr[@itemprop="openingHours"]/@content').extract()

        for hour in hours:
            if hour.split()[-1].lower() == "closed":
                continue
            else:
                day, open_time, close_time = re.search(
                    r"([a-z]{2})\s([0-9:]+)-([0-9:]+)", hour, flags=re.IGNORECASE
                ).groups()
                opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r".+/(.+).html", response.url).group(1)

        properties = {
            "street_address": response.xpath('//span[@class="c-address-street-1"]/text()').extract_first().strip(),
            "city": response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
            "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "name": response.xpath('//span[@class="location-geomodifier"]/text()').extract_first(),
        }

        hours = self.parse_hours(response.xpath('//div[@class="c-location-hours"]//tbody'))

        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()
        is_store_list = response.xpath('//div[@class="location-list-container"]').extract()

        if not urls and is_store_list:
            urls = response.xpath(
                '//div[@class="location-list-container"]//a[text()="View Store Details"]/@href'
            ).extract()
        for url in urls:
            if url.count("/") >= 2:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
