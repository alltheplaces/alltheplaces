import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "SUNDAY": "Su",
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
}


class MacysSpider(scrapy.Spider):
    name = "macys"
    item_attributes = {"brand": "Macy's", "brand_wikidata": "Q629269"}
    allowed_domains = ["macys.com"]
    download_delay = 0.2
    start_urls = ("https://l.macys.com/",)

    def parse_hours(self, hours):
        hours = json.loads(hours)
        opening_hours = OpeningHours()

        for hour in hours:
            if not hour["isClosed"]:
                opening_hours.add_range(
                    day=DAY_MAPPING[hour["day"]],
                    open_time=str(hour["intervals"][0]["start"]),
                    close_time=str(hour["intervals"][0]["end"]),
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath('//div[@class="Directory-content"]//li/a/@href').extract()

        if not urls:
            urls = response.xpath(
                '//div[@class="Directory-content"]//li//a[contains(text(), "Store Details")]/@href'
            ).extract()
        for url in urls:
            if ".html" not in url:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))

    def parse_store(self, response):
        brand = response.xpath('//span[@class="LocationName-brand"]/text()').extract_first()
        name = response.xpath('//span[@class="LocationName-geo"]/text()').extract_first()

        properties = {
            "name": brand + " " + name,
            "street_address": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            "ref": re.search(r".*/(.*)$", response.url).groups()[0],
            "lat": response.xpath('//span[@class="coordinates"]/meta[@itemprop="latitude"]/@content').extract_first(),
            "lon": response.xpath('//span[@class="coordinates"]/meta[@itemprop="longitude"]/@content').extract_first(),
            "phone": response.xpath('//div[@itemprop="telephone"]//a/text()').extract_first(),
            "website": response.url,
        }
        hours = self.parse_hours(response.xpath('//span[contains(@class, "c-hours-today")]/@data-days').extract_first())

        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)
