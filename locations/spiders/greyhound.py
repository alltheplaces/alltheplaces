# -*- coding: utf-8 -*-
import re
from urllib.parse import urlencode

import scrapy

from locations.items import GeojsonPointItem


class GreyhoundSpider(scrapy.Spider):
    name = "greyhound"
    item_attributes = {"brand": "Greyhound"}
    allowed_domains = ["locations.greyhound.com"]
    start_urls = [
        "https://locations.greyhound.com/",
    ]
    download_delay = 0.3

    def start_requests(self):
        url = "https://locations.greyhound.com/getCitiesJson?"

        yield scrapy.http.Request(url, self.parse, method="GET")

    def parse(self, response):
        search_url = "https://locations.greyhound.com/bus-stations/search?"

        locations = response.json()
        for location in locations.values():
            city, state = location.split(", ")
            params = {
                "city": "{}".format(city),
                "state": "{}".format(state),
            }

            yield scrapy.http.Request(
                search_url + urlencode(params), callback=self.parse_location_list
            )

    def parse_location_list(self, response):
        location_urls = response.xpath(
            '//div[@class="col-md-6 col-xs-8 station_city_info"]/a/@href'
        ).extract()
        for location_url in location_urls:
            yield scrapy.http.Request(
                response.urljoin(location_url), callback=self.parse_location
            )

    def parse_location(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        name = response.xpath('//span[@class="station-title"]/text()').extract_first()
        location_type = response.xpath(
            'normalize-space(//*/text()[normalize-space(.)="Location Type:"]/following::text())'
        ).extract_first()
        address = response.xpath(
            'normalize-space(//*/text()[normalize-space(.)="Address:"]/following::text())'
        ).extract_first()
        city_state_zip = response.xpath(
            'normalize-space(//*/text()[normalize-space(.)="City, State Zip:"]/following::text())'
        ).extract_first()
        match = re.search(r"([\w\s]+),\s(\w+)\s(\w+)", city_state_zip)
        city, state, postcode = match.groups()
        country = re.search(
            r".+/(.+?)/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url
        ).groups()[0]
        phone = response.xpath(
            'normalize-space(//*/text()[normalize-space(.)="Main:"]/following::text())'
        ).extract_first()

        # Get coordinates
        map_data = response.xpath(
            '//script[@type="text/javascript"][contains(text(), "new L.LatLng")]/text()'
        ).extract_first()
        coordinates = re.search(
            r"new L.Marker\(new L.LatLng\((.*)\)\);", map_data
        ).groups()[0]
        lat, lon = coordinates.split(", ")

        properties = {
            "ref": ref,
            "name": name,
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
            "lat": lat,
            "lon": lon,
            "phone": phone,
            "website": response.url,
            "extras": {"location_type": location_type},
        }

        yield GeojsonPointItem(**properties)
