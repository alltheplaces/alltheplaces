import json

import scrapy

from locations.items import Feature


class LifetimeSpider(scrapy.Spider):
    name = "lifetimefitness"
    item_attributes = {"brand": "Lifetime", "brand_wikidata": "Q6545004"}
    allowed_domains = ["lifetime.life"]
    start_urls = ("https://www.lifetime.life/view-all-locations.html",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath(
            '//a[@class="btn btn-link btn-xs m-b-sm p-x-0 b-x-xs-0 pull-xs-right"]/@href'
        ).extract()
        for path in city_urls:
            yield scrapy.Request(
                "https://www.lifetime.life" + path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        json_data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        data = json.loads(json_data)

        properties = {
            "name": data["name"],
            "ref": data["name"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data["telephone"],
            "website": data["url"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
        }

        yield Feature(**properties)
