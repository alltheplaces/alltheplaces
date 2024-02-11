import json
import re

import scrapy

from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosZWSpider(scrapy.Spider):
    name = "nandos_zw"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["www.nandos.co.zw"]
    start_urls = [
        "https://www.nandos.co.zw/eat/restaurants-all",
    ]
    download_delay = 0.3

    def parse(self, response):
        urls = response.xpath('//ul[@class="row row-fixed-cols list-unstyled restaurant-list"]/li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(url=response.urljoin(url.strip()), callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "address")]/text()'
        ).extract_first()

        if data:
            store_data = json.loads(data)
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

            properties = {
                "name": store_data["name"],
                "ref": ref,
                "addr_full": store_data["address"]["streetAddress"],
                "city": store_data["address"]["addressLocality"],
                "state": store_data["address"]["addressRegion"],
                "postcode": store_data["address"]["postalCode"],
                "phone": store_data["contactPoint"][0].get("telephone"),
                "website": response.url,
                "country": "ZW",
                "lat": store_data["geo"]["latitude"],
                "lon": store_data["geo"]["longitude"],
            }

            yield Feature(**properties)
