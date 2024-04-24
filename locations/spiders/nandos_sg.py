import re

import scrapy

from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosSGSpider(scrapy.Spider):
    name = "nandos_sg"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["nandos.com.sg"]
    start_urls = [
        "https://www.nandos.com.sg/restaurants/",
    ]
    download_delay = 0.3

    def parse(self, response):
        urls = response.xpath('//div[@class="restaurant col-xs-12 col-sm-6 col-md-4"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        restaurant_data = response.xpath(
            '//div[@class="restaurant-details-wrapper"]/script[contains(text(),"var restaurant")]'
        ).extract_first()
        lat, lon = re.search(r"var restaurant = {.*: (.*), .*: (.*)}", restaurant_data).groups()

        properties = {
            "ref": ref,
            "name": response.xpath('//div[@class="promo-pane-title"]/h2/text()').extract_first(),
            "addr_full": response.xpath('//div[@class="copy"]/h5/text()').extract_first(),
            "country": "SG",
            "lat": lat,
            "lon": lon,
            "website": response.url,
        }

        yield Feature(**properties)
