import json
import re

import scrapy

from locations.items import Feature


class LivingSpacesSpider(scrapy.Spider):
    name = "living_spaces"
    item_attributes = {"brand": "Living Spaces", "brand_wikidata": "Q63626177"}
    allowed_domains = ["livingspaces.com"]
    start_urls = ("https://www.livingspaces.com/stores",)

    def parse(self, response):
        urls = response.xpath('//div[@class="st-detail"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first()
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        if data:
            store_data = json.loads(data)

            properties = {
                "ref": ref,
                "name": response.xpath('//h1[@class="page-title"]/text()').extract_first().strip(),
                "addr_full": store_data["address"]["streetAddress"],
                "city": store_data["address"]["addressLocality"],
                "state": store_data["address"]["addressRegion"],
                "postcode": store_data["address"]["postalCode"],
                "country": store_data["address"]["addressCountry"],
                "phone": store_data.get("telephone"),
                "lat": float(store_data["geo"]["latitude"]),
                "lon": float(store_data["geo"]["longitude"]),
                "website": store_data.get("url"),
            }

            yield Feature(**properties)

        else:
            pass
