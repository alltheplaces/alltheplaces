# -*- coding: utf-8 -*-
import logging

import scrapy

from locations.items import GeojsonPointItem
class LidlDESpider(scrapy.Spider):
    name = "lidl_de"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["lidl.de"]
    handle_httpstatus_list = [404]
    start_urls = ["https://www.lidl.de/f/"]
    def parse_details(self, response):

        lidlShops = response.css('.ret-o-store-detail')

        for shop in lidlShops:
            shopAddress = shop.css('.ret-o-store-detail__address::text').extract()
            street = shopAddress[0]
            postalCode = shopAddress[1].split()[0]
            city = shopAddress[1].split()[1]

            openingHours = shop.css('.ret-o-store-detail__opening-hours::text').extract()
            shopOpeningHours = {}
            for openingHour in openingHours:
                if(openingHour.split()):
                    day = openingHour.split()[0]
                    hours = openingHour.split()[1]
                    shopOpeningHours[day] = hours

            services = response.css('.ret-o-store-detail__store-icon-wrapper')[0]
            link = services.css('a::attr("href")').get()
            coordinates = link.split('pos.')[1].split('_L')[0]
            latitude = coordinates.split('_')[0]
            longitude = coordinates.split('_')[1]

            properties = {
                "ref": latitude+longitude,
                "country": "Germany",
                "name": "Lidl",
                "street": street,
                "postcode": postalCode,
                "city": city,
                "opening_hours": shopOpeningHours,
                "lat": latitude,
                "lon": longitude
            }
            yield GeojsonPointItem(**properties)

    def parse(self, response):
        # Read all provinces
        provinces = response.css('.ret-o-store-detail-content')
        print(sys.path)

        # Read cities in each province
        for province in provinces:
            cities = province.css('.ret-o-store-detail-city').css('a::attr(href)')


            for city in cities:
                logging.info(f"Processing for url {city.get()}")
                city = f"https://www.lidl.de{city.get()}"

                yield scrapy.Request(url=city, callback=self.parse_details)
