import re

import scrapy

from locations.items import Feature


class FloorAndDecorSpider(scrapy.Spider):
    name = "floor_and_decor"
    item_attributes = {"brand": "Floor and Decor", "brand_wikidata": "Q56280964"}
    allowed_domains = ["www.flooranddecor.com"]
    start_urls = [
        "https://www.flooranddecor.com/view-all-stores",
    ]
    download_delay = 0.3

    def parse(self, response):
        store_urls = re.findall(r"<div class='store-footer'><a href='(.*)'>", response.text)

        for store_url in store_urls:
            yield scrapy.Request(store_url, callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r"StoreID=([0-9]+)$", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath('normalize-space(//div[@class="name"]/h1/text())').extract_first(),
            "addr_full": response.xpath('normalize-space(//span[@itemprop="streetAddress"]//text())').extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())')
            .extract_first()
            .strip(","),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]//text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }

        yield Feature(**properties)
