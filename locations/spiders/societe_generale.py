# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class SocieteGeneraleSpider(scrapy.Spider):
    name = "societe_generale"
    item_attributes = {'brand': 'Societe Generale', 'brand_wikidata': 'Q270363'}
    allowed_domains = ["societegenerale.com"]
    start_urls = [
        'https://www.societegenerale.com/en/about-us/our-businesses/our-locations',
    ]

    def parse(self, response):
        template = 'https://www.societegenerale.com/implentation/map-filter?lang=en-soge&country={country}&job=allmet&entity=allent'


        countries = response.xpath('//select[@id="country"]/optgroup/option/text()').extract()

        for country in countries:
            if country == "All countries":
                pass
            else:
                url = template.format(country=country)
                yield scrapy.Request(url, callback=self.parse_location)


    def parse_location(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data["markers"]["places"]
        try:
            store_data = stores[0]
            properties = {
                'name': store_data["name"],
                'ref': store_data["id"],
                'addr_full': store_data["address"],
                'city': store_data["city"],
                'country': store_data["country"],
                'phone': store_data["phone"],
                'lat': float(store_data["latitude"]),
                'lon': float(store_data["longitude"]),
                'website': store_data["url"]
            }

            yield GeojsonPointItem(**properties)
        except:
            pass