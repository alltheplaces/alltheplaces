import json
import re

import scrapy

from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosOMSpider(scrapy.Spider):
    name = "nandos_om"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["www.nandosoman.com"]
    start_urls = [
        "https://www.nandosoman.com/eat/restaurants-all",
    ]

    def parse(self, response):
        urls = response.xpath('//div[@class="row"]/a/@href').extract()

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
                "country": "OM",
                "lat": store_data["geo"]["latitude"],
                "lon": store_data["geo"]["longitude"],
            }

            yield Feature(**properties)
