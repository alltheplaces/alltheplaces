import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class LensCraftersSpider(scrapy.Spider):
    name = "lenscrafters"
    item_attributes = {"brand": "Lenscrafters", "brand_wikidata": "Q6523209"}
    allowed_domains = ["local.lenscrafters.com"]
    start_urls = ["https://local.lenscrafters.com/"]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for group in hours:
            if "Closed" in group:
                pass
            else:
                days, open_time, close_time = re.search(r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)", group).groups()
                days = days.split(",")
                for day in days:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink Link--directory"]/@href').extract()

        # If cannot find 'Directory-listLink Link--directory' then this is a store page
        if len(urls) == 0:
            properties = {
                "name": response.xpath('//h1[@id="location-name"]/text()').extract_first(),
                "street_address": response.xpath('//span[@class="c-address-street-1"]/text()').extract_first(),
                "city": response.xpath('//span[@class="c-address-city"]/text()').extract_first(),
                "state": response.xpath('//abbr[@class="c-address-state"]/text()').extract_first(),
                "postcode": response.xpath('//span[@class="c-address-postal-code"]/text()').extract_first(),
                "phone": response.xpath('//div[@id="phone-main"]/text()').extract_first(),
                "ref": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
                "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
                "lat": response.xpath('//meta[@itemprop="latitude"]/@content').extract_first(),
                "lon": response.xpath('//meta[@itemprop="longitude"]/@content').extract_first(),
            }

            hours = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
        else:
            for path in urls:
                yield scrapy.Request(url=response.urljoin(path), callback=self.parse)
