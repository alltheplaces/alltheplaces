# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class PandaSpider(scrapy.Spider):
    name = "pandaexpress"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    allowed_domains = ["pandaexpress.com"]
    start_urls = ["https://www.pandaexpress.com/locations"]

    def parse(self, response):
        for href in response.xpath(
            '//a[@data-ga-action="locationClick" or @data-ag-action="storeDetailsClick"]/@href'
        ).extract():
            yield scrapy.Request(response.urljoin(href))

        if response.xpath("//@data-productlink"):
            slug = response.xpath("//@data-productlink").get().split("/")[2]
            if slug:
                url = f"https://nomnom-prod-api.pandaexpress.com/restaurants/byslug/{slug}"
                yield scrapy.Request(
                    url, meta={"url": response.url}, callback=self.parse_store
                )

    def parse_store(self, response):
        data = response.json()
        url = response.meta["url"]
        properties = {
            "ref": data["id"],
            "lat": data["latitude"],
            "lon": data["longitude"],
            "name": data["name"],
            "website": url,
            "addr_full": data["streetaddress"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["zip"],
            "country": data["country"],
            "phone": data["telephone"],
        }
        yield GeojsonPointItem(**properties)
