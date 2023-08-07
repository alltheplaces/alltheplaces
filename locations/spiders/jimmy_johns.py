import json

import scrapy

from locations.items import Feature


class JimmyJohnsSpider(scrapy.Spider):
    name = "jimmy_johns"
    item_attributes = {"brand": "Jimmy John's", "brand_wikidata": "Q1689380"}
    allowed_domains = ["locations.jimmyjohns.com"]
    start_urls = ("https://locations.jimmyjohns.com/sitemap.xml",)

    def parse(self, response):
        stores = response.xpath('//url/loc[contains(text(),"sandwiches")]/text()').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]//text()').extract_first())

        properties = {
            "ref": data[0]["url"],
            "street_address": data[0]["address"]["streetAddress"],
            "city": data[0]["address"]["addressLocality"],
            "state": data[0]["address"]["addressRegion"],
            "postcode": data[0]["address"]["postalCode"],
            "website": response.url,
            "lat": data[0]["geo"]["latitude"],
            "lon": data[0]["geo"]["longitude"],
        }
        if data[0]["address"]["telephone"]:
            properties["phone"] = data[0]["address"]["telephone"]

        yield Feature(**properties)
