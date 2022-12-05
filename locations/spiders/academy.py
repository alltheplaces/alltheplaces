import re

import scrapy
from scrapy.utils.gz import gunzip

from locations.items import GeojsonPointItem


class AcademySpider(scrapy.Spider):
    name = "academy"
    item_attributes = {
        "brand": "Academy Sports + Outdoors",
        "brand_wikidata": "Q4671380",
    }
    allowed_domains = []
    start_urls = [
        "https://www.academy.com/sitemap_store_1.xml.gz",
    ]

    def parse(self, response):
        body = gunzip(response.body)
        body = scrapy.Selector(text=body)
        body.remove_namespaces()
        urls = body.xpath("//url/loc/text()").extract()
        store_url = re.compile(
            r"https://www.academy.com/storelocator/.+?/.+?/store-\d+"
        )
        for path in urls:
            if re.search(store_url, path):
                yield scrapy.Request(path.strip(), callback=self.parse_store)

    def parse_store(self, response):
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath(
                'normalize-space(//*[@class="Hero-name"]//text())'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//*[@class="c-address-street-1"]//text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//*[@class="c-address-city"]//text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//*[@class="c-address-state"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]//text())'
            ).extract_first(),
            "phone": response.xpath('normalize-space(//*[@class="Phone-link"]//text())').extract_first(),
            "website": response.url,
            "lat": float(
                    response.xpath('normalize-space(//*[@itemprop="latitude"]/@content)').extract_first()
                ),
            "lon": float(
                    response.xpath('normalize-space(//*[@itemprop="longitude"]/@content)').extract_first()
                )
        }

        properties["opening_hours"] = "; ".join(response.xpath('//*[@itemprop="openingHours"]/@content').extract())

        yield GeojsonPointItem(**properties)
