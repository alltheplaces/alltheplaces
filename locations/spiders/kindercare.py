import json

import scrapy

from locations.items import Feature


class KindercareSpider(scrapy.Spider):
    name = "kindercare"
    item_attributes = {
        "brand": "KinderCare Learning Centers",
        "brand_wikidata": "Q6410551",
    }
    allowed_domains = ["kindercare.com"]
    start_urls = [
        "https://www.kindercare.com/our-centers",
    ]
    download_delay = 0.5

    def parse_location(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        properties = {
            "name": data["name"],
            "ref": data["@id"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "website": response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//div[contains(@class, "link-index-results")]//li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)
