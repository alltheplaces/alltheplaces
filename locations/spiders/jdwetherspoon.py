import re

import scrapy

from locations.items import Feature


class JDWetherspoonSpider(scrapy.Spider):
    name = "jdwetherspoon"
    item_attributes = {"brand": "Wetherspoon", "brand_wikidata": "Q6109362"}
    allowed_domains = ["jdwetherspoon.com"]
    start_urls = ("https://www.jdwetherspoon.com/pubs/all-pubs/",)

    def parse(self, response):
        urls = response.xpath('//li[@class="advanced-listing-results__item"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "ref": ref.strip("/"),
            "addr_full": response.xpath('normalize-space(//span[@itemprop="streetAddress"])').extract()[0],
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            "phone": response.xpath('//span[@class="location-block__telephone--ie"]/text()').extract_first(),
            "name": response.xpath('//h1[@class="banner-inner__title"]/text()').extract_first(),
            "country": "GB",
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "website": response.url,
        }

        yield Feature(**properties)
