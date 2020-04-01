# -*- coding: utf-8 -*-
import scrapy

from functools import partial
from scrapy.http import FormRequest
from locations.items import GeojsonPointItem


class RoadysSpider(scrapy.Spider):
    name = "roadys"
    allowed_domains = ["roadys.com"]

    def start_requests(self):
        return [ FormRequest("https://roadys.com/wp-content/plugins/roadys-locations/getLocations.php",
                     formdata={'lat': '1', 'lon': '1'},
                     callback=self.parse) ]

    def parse_location(self, lid, response):
        single_rloc = response.xpath('//div[@class="single rloc"]')[0]

        # location name
        title = single_rloc.xpath('.//div[@class="rloc_title"]/text()').extract_first()

        # location address
        addr_full, city_state_postcode = single_rloc.xpath('.//div[@class="rloc_address"]//text()').extract()
        addr_full = addr_full.strip()
        city, state_postcode = city_state_postcode.rsplit(",", 1)
        city = city.strip()
        state_postcode = state_postcode.strip()
        if " " in state_postcode:
          state, postcode = state_postcode.split(" ")
          state = state.strip()
          postcode = postcode.strip()
        else:
          state = state_postcode
          postcode = None

        # lat/lng coordinates
        rloc_address = response.xpath('//div[@class="rloc_address"]/text()')[-1].extract()
        latitude, longitude = rloc_address.split(",")
        latitude = float(latitude)
        longitude = float(longitude)

        properties = {
            'ref': lid,
            'name': title,
            'lon': longitude,
            'lat': latitude,
        }
        if addr_full:
            properties["addr_full"] = addr_full
        if city:
            properties["city"] = city
        if state:
            properties["state"] = state
        if postcode:
            properties["postcode"] = postcode
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//a[contains(@href, "/location/")]/@href').extract()
        # urls are in the form like
        # "/location/193/Hamilton-AL/Roadys-Moores-Shell-Super-Store"
        # so pull out the 193
        lids = [url.split("/")[2] for url in urls]

        for lid in lids:
            yield FormRequest(
                "https://roadys.com/wp-content/plugins/roadys-locations/getSingleLocation.php",
                formdata={'lid': lid},
                callback=partial(self.parse_location, lid),
            )
