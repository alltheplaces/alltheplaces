import json

import scrapy

from locations.categories import Categories
from locations.items import Feature


class ChicosOffTheRackSpider(scrapy.Spider):
    name = "chicosofftherack"
    item_attributes = {
        "brand": "Chico's Off The Rack",
        "brand_wikidata": "Q5096393",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    allowed_domains = ["stores.chicosofftherack.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        pages = [*range(0, 30, 1)]
        for page in pages:
            url = "https://chicosofftherack.brickworksoftware.com/locations_search?page=0&filters=domain:chicosofftherack.brickworksoftware.com+AND+publishedAt%3C%3D1607530828107&esSearch=%7B%22page%22:{page},%22storesPerPage%22:50,%22domain%22:%22chicosofftherack.brickworksoftware.com%22,%22locale%22:%22en_US%22,%22must%22:[%7B%22type%22:%22range%22,%22field%22:%22published_at%22,%22value%22:%7B%22lte%22:1607530828107%7D%7D],%22filters%22:[],%22aroundLatLngViaIP%22:false%7D".format(
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
                "street_address": data["attributes"]["address1"],
                "city": data["attributes"]["city"],
                "state": data["attributes"]["state"],
                "postcode": data["attributes"]["postalCode"],
                "country": data["attributes"]["countryCode"],
                "website": "https://stores.chicosofftherack.com/s/" + data["attributes"]["slug"],
                "lat": float(data["attributes"]["latitude"]),
                "lon": float(data["attributes"]["longitude"]),
            }

            yield Feature(**properties)
