from scrapy import Spider
from scrapy.http import JsonRequest

from locations.items import Feature


class FishbowlAUSpider(Spider):
    name = "fishbowl_au"
    item_attributes = {"brand": "Fishbowl", "brand_wikidata": "Q110785465"}
    allowed_domains = ["fishbowl.com.au", "api.mapbox.com"]
    start_urls = ["https://fishbowl.com.au/assets/js/main.js"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        features_url = response.text.split('const t="', 1)[1].split('"', 1)[0]
        yield JsonRequest(url=features_url, callback=self.parse_locations)

    def parse_locations(self, response):
        for location in response.json()["features"]:
            properties = {
                "ref": location["id"],
                "name": location["properties"]["title"],
                "addr_full": location["properties"]["place_name"],
                "lat": location["geometry"]["coordinates"][1],
                "lon": location["geometry"]["coordinates"][0],
                "state": location["properties"]["state"].upper(),
                "image": location["properties"]["img"],
            }
            yield Feature(**properties)
