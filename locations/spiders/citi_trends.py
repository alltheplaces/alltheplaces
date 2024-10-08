import re

import scrapy

from locations.items import Feature


class CitiTrendsSpider(scrapy.Spider):
    name = "citi_trends"
    item_attributes = {"brand": "Citi Trends", "brand_wikidata": "Q5122438"}
    allowed_domains = ["locations.cititrends.com"]
    start_urls = ("https://locations.cititrends.com/",)

    def parse_stores(self, response):
        properties = {
            "street_address": response.xpath(
                'normalize-space(//span[@class="c-address-street-1"]/text())'
            ).extract_first(),
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            "ref": re.findall(r"[a-z]{2}\/[^()]+\/[^.]+", response.url)[0].replace("/", "_"),
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }

        hours = response.xpath('//div[@itemprop="openingHours"]/@content').extract()
        hours = "; ".join(hours)
        if hours:
            properties["opening_hours"] = hours
        yield Feature(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//h2[@class="c-location-grid-item-title"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in city_urls:
            pattern1 = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if pattern1.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}.html$")
            pattern1 = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif pattern1.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
