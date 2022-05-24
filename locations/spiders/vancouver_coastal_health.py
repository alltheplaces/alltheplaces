# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem

BASE_URL = (
    "http://www.vch.ca/_api/Web/Lists(guid'51d09f82-eddf-47c9-95e9-9f5f0ec838c5')/"
)


class VancouverCoastalHealthSpider(scrapy.Spider):
    name = "vancouver_coastal_health"
    item_attributes = {
        "brand": "Vancouver Coastal Health",
        "brand_wikidata": "Q7914144",
    }
    allowed_domains = ["www.vch.ca"]
    start_urls = [
        "http://www.vch.ca/StaticDirectoryPages/sitemap1.xml",
    ]
    download_delay = 0.5

    def parse(self, response):
        response.selector.remove_namespaces()

        locations = response.xpath("//url/loc/text()").extract()
        location_ids = [
            re.search(r"\/([0-9]+)\.aspx", location_id).group(1)
            for location_id in locations
        ]
        urls = [BASE_URL + f"Items({location_id})" for location_id in location_ids]

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_location)

    def parse_location(self, response):
        response.selector.remove_namespaces()
        ref = response.xpath("//ID/text()").extract_first()
        coords = response.xpath("//Geocode/text()").extract_first()
        if coords:
            lat, lon = coords.split(",")
            if float(lat) < 45.0:
                lat, lon = None, None
        else:
            lat = None
            lon = None
        city = response.xpath("//City_x0020_Field/text()").extract_first()
        if city == "[blank]":
            city = None
        phone_str = response.xpath("//Phone_x0020_1/text()").extract_first()
        if phone_str:
            phone = "".join(re.findall(r"([0-9]+)", phone_str))
        else:
            phone = None
        website = "http://www.vch.ca/Locations-Services/result?res_id=" + ref

        properties = {
            "ref": ref,
            "name": response.xpath("//Specific_x0020_Title/text()").extract_first(),
            "addr_full": response.xpath("//Address_x0020_1/text()").extract_first(),
            "city": city,
            "state": response.xpath("//Province/text()").extract_first(),
            "postcode": response.xpath("//Postal_x0020_Code/text()").extract_first(),
            "country": "CA",
            "lat": lat,
            "lon": lon,
            "phone": phone,
            "website": website,
        }

        yield GeojsonPointItem(**properties)
