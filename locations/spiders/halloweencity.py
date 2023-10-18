import json

import scrapy

from locations.items import Feature


class HalloweenCitySpider(scrapy.Spider):
    name = "halloween_city"
    item_attributes = {"brand": "Halloween City"}
    download_delay = 0.2
    allowed_domains = ("stores.halloweencity.com",)
    start_urls = ("http://stores.halloweencity.com/",)

    def parse_stores(self, response):
        app_json = json.loads(
            response.xpath('normalize-space(//script[contains(text(), "markerData")]/text())').re_first(
                r"RLS.defaultData = (\{.*?\});"
            )
        )
        store = json.loads(
            scrapy.Selector(text=app_json["markerData"][0]["info"]).xpath("//div/text()").extract_first()
        )

        props = {
            "name": store["location_name"],
            "addr_full": store["address_1"],
            "city": store["city"],
            "state": store["region"],
            "postcode": store["post_code"],
            "phone": store["local_phone_dashes"],
            "lat": float(app_json["markerData"][0]["lat"]),
            "lon": float(app_json["markerData"][0]["lng"]),
            "ref": store["fid"],
            "website": store["url"],
        }

        return Feature(**props)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@class="map-list-item-section map-list-item-top"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)
        if not stores:
            yield self.parse_stores(response)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="map-list-item is-single"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="map-list-item is-single"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
