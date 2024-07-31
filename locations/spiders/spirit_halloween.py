import json
import re

import scrapy

from locations.items import Feature


class SpiritHalloweenSpider(scrapy.Spider):
    name = "spirit_halloween"
    item_attributes = {"brand": "Spirit Halloween", "brand_wikidata": "Q25212133"}
    allowed_domains = ("stores.spirithalloween.com",)
    start_urls = ("http://stores.spirithalloween.com/",)

    def parse_stores(self, response):
        app_json = json.loads(
            response.xpath('normalize-space(//script[@type="application/ld+json"]/text())').extract_first()
        )
        hours = app_json[0]["openingHours"].replace(" - ", "-").split()
        hours = [re.sub(r"[:]$", "", day_hour) for day_hour in hours]

        props = {
            "addr_full": app_json[0]["address"]["streetAddress"],
            "city": app_json[0]["address"]["addressLocality"],
            "state": app_json[0]["address"]["addressRegion"],
            "postcode": app_json[0]["address"]["postalCode"],
            "phone": app_json[0]["address"]["telephone"],
            "lat": float(app_json[0]["geo"]["latitude"]),
            "lon": float(app_json[0]["geo"]["longitude"]),
            "opening_hours": "; ".join(["{} {}".format(x[0], x[1]) for x in zip(*[iter(hours)] * 2)]),
            "ref": response.url,
            "name": app_json[0]["mainEntityOfPage"]["breadcrumb"]["itemListElement"][0]["item"]["name"],
            "website": response.url,
        }

        return Feature(**props)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@class="map-list-item-info"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="map-list-item is-single"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="map-list-item is-single"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
