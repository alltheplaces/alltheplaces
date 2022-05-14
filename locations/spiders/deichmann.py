# -*- coding: utf-8 -*-
import scrapy
import json
import base64
from locations.items import GeojsonPointItem


class Deichmann(scrapy.Spider):
    name = "deichmann"
    item_attributes = {"brand": "Deichmann", "brand_wikidata": "Q664543"}
    allowed_domains = ["stores.deichmann.com", "stores.dosenbach.ch"]
    start_urls = ("https://stores.deichmann.com/index.html",)

    def parse(self, response):
        # base url of all countries
        countries = response.xpath(
            '//ul[@class="countrydropdown"]/li/a/@href'
        ).extract()

        for country in countries:
            yield scrapy.Request(country, callback=self.parse_country)

    def parse_country(self, response):
        # parse country per region
        cities = response.xpath('//a[@class="region-list__link"]/@href').extract()

        for city in cities:
            yield scrapy.Request(response.urljoin(city), callback=self.parse_city)

    def parse_city(self, response):
        # parse cities in region
        stores = response.xpath('//a[@class="button-link"]/@href').extract()

        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_locations)

    def parse_locations(self, response):
        # get json which provides all data
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()

        try:
            if data:
                data = json.loads(data)

                geo_data = data.get("geo", {})
                address_data = data.get("address", {})
                contact_data = data.get("ContactPoint", {})

                properties = {
                    "ref": data.get("@id", None),
                    "name": data.get("name", None),
                    "lat": geo_data.get("latitude", None),
                    "lon": geo_data.get("longitude", None),
                    "phone": contact_data[0].get("telephone", None),
                    "addr_full": address_data.get("streetAddress", None),
                    "country": address_data.get("addressCountry", None),
                    "postcode": address_data.get("postalCode", None),
                    "city": address_data.get("addressLocality", None),
                    "opening_hours": data.get("openingHours", None),
                }

                yield GeojsonPointItem(**properties)
        except Exception as e:
            self.logger.warn("----------------- Error -----------------: {}".format(e))
            pass
