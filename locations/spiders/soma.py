# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class SomaSpider(scrapy.Spider):
    name = "soma"
    item_attributes = {"brand": "Soma"}
    allowed_domains = ["stores.soma.com"]

    def start_requests(self):
        pages = [*range(0, 30, 1)]
        for page in pages:
            url = "https://soma.brickworksoftware.com/locations_search?page=0&filters=domain:soma.brickworksoftware.com+AND+publishedAt%3C%3D1607532724190&esSearch=%7B%22page%22:{page},%22storesPerPage%22:50,%22domain%22:%22soma.brickworksoftware.com%22,%22locale%22:%22en_US%22,%22must%22:[%7B%22type%22:%22range%22,%22field%22:%22published_at%22,%22value%22:%7B%22lte%22:1607532724190%7D%7D],%22filters%22:[],%22aroundLatLngViaIP%22:false%7D".format(
                page=page
            )
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        jsonresponse = response.json()
        locations = jsonresponse["hits"]
        for location in locations:
            location_data = json.dumps(location)
            data = json.loads(location_data)

            properties = {
                "name": data["attributes"]["name"],
                "ref": data["id"],
                "addr_full": data["attributes"]["address1"],
                "city": data["attributes"]["city"],
                "state": data["attributes"]["state"],
                "postcode": data["attributes"]["postalCode"],
                "country": data["attributes"]["countryCode"],
                "website": "https://stores.soma.com/s/" + data["attributes"]["slug"],
                "lat": float(data["attributes"]["latitude"]),
                "lon": float(data["attributes"]["longitude"]),
            }

            yield GeojsonPointItem(**properties)
