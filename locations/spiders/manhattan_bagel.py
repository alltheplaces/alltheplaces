import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ManhattanBagelSpider(scrapy.Spider):
    """Copy of Einstein Bros. Bagels - all brands of the same parent company Coffee & Bagels"""

    name = "manhattan_bagel"
    item_attributes = {"brand": "Manhattan Bagel", "brand_wikidata": "Q64517333"}
    allowed_domains = ["manhattanbagel.com"]
    start_urls = ("https://locations.manhattanbagel.com/us",)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for elem in elements:
            day = elem.xpath('.//td[@class="c-location-hours-details-row-day"]/text()').extract_first()
            intervals = elem.xpath('.//td[@class="c-location-hours-details-row-intervals"]')

            if intervals.xpath("./text()").extract_first() == "Closed":
                continue
            if intervals.xpath("./span/text()").extract_first() == "Open 24 hours":
                opening_hours.add_range(day=day, open_time="0:00", close_time="23:59")
            else:
                start_time = elem.xpath(
                    './/span[@class="c-location-hours-details-row-intervals-instance-open"]/text()'
                ).extract_first()
                end_time = elem.xpath(
                    './/span[@class="c-location-hours-details-row-intervals-instance-close"]/text()'
                ).extract_first()
                opening_hours.add_range(day=day[:2], open_time=start_time, close_time=end_time, time_format="%I:%M %p")

        return opening_hours

    def parse_store(self, response):
        ref = re.search(r".+/(.+)$", response.url).group(1)

        address1 = response.xpath('//span[@class="c-address-street-1"]/text()').extract_first()
        address2 = response.xpath('//span[@class="c-address-street-2"]/text()').extract_first() or ""

        properties = {
            "street_address": merge_address_lines([address1, address2]),
            "phone": response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            "city": response.xpath('//span[@class="c-address-city"]/text()').extract_first(),
            "state": response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "name": response.xpath('//h1[@id="location-name"]/text()').extract_first(),
        }

        hours = self.parse_hours(response.xpath('//table[@class="c-location-hours-details"]//tbody/tr'))

        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        is_store_list = response.xpath('//section[contains(@class,"LocationList")]').extract()

        if not urls and is_store_list:
            urls = response.xpath('//a[contains(@class,"Teaser-titleLink")]/@href').extract()

        for url in urls:
            if re.search(r"us/.{2}/.+/.+", url):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
