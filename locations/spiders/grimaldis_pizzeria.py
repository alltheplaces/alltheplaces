# -*- coding: utf-8 -*-
import re
import scrapy
from collections import namedtuple
from locations.items import GeojsonPointItem


class GrimaldisPizzeriaSpider(scrapy.Spider):
    name = "grimaldis_pizzeria"
    item_attributes = {"brand": "Grimaldi's Pizzeria", "brand_wikidata": "Q564256"}
    allowed_domains = ["www.grimaldispizzeria.com"]
    start_urls = ("https://www.grimaldispizzeria.com/locations/",)

    def parse(self, response):
        # Get coordinates embedded in script tag
        script = response.css("script:contains('stateLatLngs')::text").get()
        coordinates = {}
        for latlng in re.findall(r"latlng:.(.*?https.*?),", script):
            lat = re.search(r"lat: (.+?),", latlng).group(1)
            long = re.search(r"lng: (.+?)},", latlng).group(1)
            website = re.search(r"'(https.*)'", latlng).group(1)
            coordinates[website] = [lat, long]

        # Get location data from each location block
        locations = response.css("div.location_block")
        for loc in locations:
            address = self._format_address(loc.css(".store_address::text").getall())
            website = loc.css(
                ".cta_row .cta_button:last-child .g_cta::attr(href)"
            ).get()

            properties = {
                "ref": website.split("/")[-2],
                "name": loc.css(".loc_title::text").get(),
                "street_address": address.street_address,
                "city": address.city,
                "state": address.state,
                "postcode": address.zip,
                "phone": self._format_phone(loc.css(".phone_number::text")),
                "opening_hours": self._format_store_hours(
                    loc.css(".store_hours::text").getall()
                ),
                "website": website,
                "lat": coordinates[website][0],
                "lon": coordinates[website][1],
            }

            yield GeojsonPointItem(**properties)

    def _format_address(self, address):
        Address = namedtuple("Address", ["street_address", "city", "state", "zip"])
        street_address = address[0].strip()
        city_state_zip = address[1].split(",")
        city = city_state_zip[0].replace(",", "")
        state, zip = city_state_zip[1].split()

        return Address(street_address=street_address, city=city, state=state, zip=zip)

    def _format_phone(self, phone):
        # if phone number is found
        if phone.getall():
            return phone.getall()[1].strip()
        else:
            return ""

    def _format_store_hours(self, hours):
        return [hour.strip() for hour in hours if hour.isspace() is False]
