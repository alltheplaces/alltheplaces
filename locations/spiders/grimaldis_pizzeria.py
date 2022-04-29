# -*- coding: utf-8 -*-
import scrapy
from collections import namedtuple
from locations.items import GeojsonPointItem


class GrimaldisPizzeriaSpider(scrapy.Spider):
    name = 'grimaldis_pizzeria'
    allowed_domains = ['www.grimaldispizzeria.com']
    start_urls = (
        'https://www.grimaldispizzeria.com/locations/',
    )

    def parse(self, response):
        locations = response.css('div.location_block')

        for loc in locations:
            address = self._format_address(loc.css('.store_address::text').getall())

            properties = {
                "ref": loc.css('h3.loc_title::text').get(),
                "name": loc.css('.loc_title::text').get(),
                "addr_full": address.street_address,
                "city": address.city,
                "state": address.state,
                "postcode": address.zip,
                "phone": self._format_phone(loc.css('.phone_number::text')),
                "opening_hours": self._format_store_hours(loc.css('.store_hours::text').getall())
            }

            yield GeojsonPointItem(**properties)

    def _format_address(self, address):
        Address = namedtuple('Address', ['street_address', 'city', 'state', 'zip'])
        street_address = address[0].strip()
        city_state_zip = address[1].split(',')
        city = city_state_zip[0].replace(',', '')
        state, zip = city_state_zip[1].split()

        return Address(
            street_address=street_address,
            city=city,
            state=state,
            zip=zip
        )

    def _format_phone(self, phone):
        # if phone number is found
        if phone.getall():
            return phone.getall()[1].strip()
        else:
            return ''

    def _format_store_hours(self, hours):
        return [hour.strip() for hour in hours if hour.isspace() is False]
