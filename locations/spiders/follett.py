# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

BASE_URL = "https://www.follett.com"


class FollettSpider(scrapy.Spider):
    name = "follett"
    item_attributes = {"brand": "Follett Corporation", "brand_wikidata": "Q5464641"}
    allowed_domains = ["www.follett.com"]
    start_urls = [
        "https://www.follett.com/college-bookstores/",
    ]
    download_delay = 0.2

    def parse(self, response):
        store_urls = response.xpath(
            '//div[@class="block-store col-lg-4 col-md-4 col-sm-6 col-xs-12 widget-block"]/h4/a/@href'
        ).extract()

        for store_url in store_urls:
            url = BASE_URL + store_url
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r"&storeid=(.+)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath(
                'normalize-space(//*[@itemprop="name"]//text())'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]//text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]//text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/following-sibling::text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]//text())'
            ).extract_first(),
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
        }

        yield GeojsonPointItem(**properties)
