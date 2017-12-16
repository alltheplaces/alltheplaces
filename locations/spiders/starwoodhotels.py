# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class StarwoodHotelsSpider(scrapy.Spider):
    name = "starwoodhotels"
    allowed_domains = ["starwoodhotels.com","usablenet.com"]
    start_urls = (
        'https://www.starwoodhotels.com/preferredguest/directory/hotels/all/list.html?language=en_US',
    )

    def parse(self, response):
        countries = response.xpath('//h5/a/@href')
        for country in countries:
            yield scrapy.Request(
                response.urljoin(country.extract()),
                callback=self.parse_country
            )

    def parse_country(self, response):
        cities = response.xpath('//h5/a/@href')
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city.extract()),
                callback=self.parse_city
            )

    def parse_city(self, response):
        hotels = response.xpath('//a[@class="propertyName"]/@href')
        for hotel in hotels:
            yield scrapy.Request(
                response.urljoin(hotel.extract()),
                callback=self.parse_hotel
            )

    def parse_hotel(self, response):
            props = {}  # some hotels don't have data because they don't opened yet

            phone = response.xpath('//li[@class="phone"]/span/text()')
            if phone:
                props['phone'] = phone.extract_first().replace('Phone:', '').strip()

            addr_full = response.xpath('//li[@class="street-address"]/span/text()')
            if addr_full:
                props['addr_full'] = addr_full.extract_first().strip()

            postcode = response.xpath('//li[@class="postal-code"]/span/text()')
            if postcode:
                props['postcode'] = postcode.extract_first().strip()

            city = response.xpath('//li[@class="city"]/span/text()')
            if city:
                props['city'] = city.extract_first().strip()

            state = response.xpath('//li[@class="region"]/span/text()')
            if state:
                props['state'] = state.extract_first().strip(),

            country = response.xpath('//li[@class="country-name"]/span/text()')
            if country:
                props['country'] = country.extract_first().strip(),

            props['lat'] = float(response.xpath('//meta[@property="og:latitude"]/@content').extract_first())
            props['lon'] = float(response.xpath('//meta[@property="og:longitude"]/@content').extract_first())
            props['website'] = response.url
            props['ref'] = response.xpath('//meta[@property="og:title"]/@content').extract_first()

            yield GeojsonPointItem(**props)
