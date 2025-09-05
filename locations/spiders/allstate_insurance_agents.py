import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class AllstateInsuranceAgentsSpider(scrapy.Spider):
    name = "allstate_insurance_agents"
    item_attributes = {"brand": "Allstate", "brand_wikidata": "Q2645636"}
    allowed_domains = ["agents.allstate.com"]
    start_urls = ("https://agents.allstate.com/",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            day, times = hour.split(" ")
            if times == "Closed":
                continue
            open_time, close_time = times.split("-")
            opening_hours.add_range(day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        properties = {
            "name": response.xpath('//span[@class="Hero-name"]/text()').extract_first(),
            "addr_full": response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            "phone": response.xpath('normalize-space(//*[@itemprop="telephone"]/@content)').extract_first(),
            "city": response.xpath('normalize-space(//meta[@itemprop="addressLocality"]/@content)').extract_first(),
            "state": response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            "ref": re.findall(r"[^\/]+$", response.url)[0].split(".")[0],
            "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "lat": float(
                response.xpath('normalize-space(//meta[@name="geo.position"]/@content)').extract_first().split(";")[0]
            ),
            "lon": float(
                response.xpath('normalize-space(//meta[@name="geo.position"]/@content)').extract_first().split(";")[1]
            ),
        }
        hours = response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
        content_hours = self.parse_hours(hours)
        if content_hours:
            properties["opening_hours"] = content_hours
        yield Feature(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//a[contains(@class, "Teaser-title")]/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        for path in city_urls:
            if re.search(r"usa\/[a-z]{2}\/[^\/]+$", path):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        for path in urls:
            if re.search(r"usa\/[a-z]{2}\/[^\/]+$", path):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
