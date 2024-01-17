import re

import scrapy

from locations.items import Feature


class MyEyeDrSpider(scrapy.Spider):
    name = "my_eye_dr"
    item_attributes = {"brand": "MyEyeDr.", "brand_wikidata": "Q117864710"}
    allowed_domains = ["myeyedr.com"]
    start_urls = [
        "https://locations.myeyedr.com/index.html",
    ]
    download_delay = 0.3

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        is_store_list = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()

        if not urls and is_store_list:
            urls = is_store_list
        for url in urls:
            if url.count("/") >= 2:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": "".join(response.xpath('//h1[@class="Hero-title"]//text()').extract()),
            "street_address": response.xpath(
                'normalize-space(//span[@class="c-address-street-1"]//text())'
            ).extract_first(),
            "city": response.xpath('normalize-space(//span[@class="c-address-city"]//text())').extract_first(),
            "state": response.xpath('normalize-space(//abbr[@class="c-address-state"]//text())').extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@class="c-address-postal-code"]//text())'
            ).extract_first(),
            "country": response.xpath('normalize-space(//abbr[@itemprop="addressCountry"]//text())').extract_first(),
            "phone": response.xpath('normalize-space(//div[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            "lon": response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
        }

        yield Feature(**properties)
