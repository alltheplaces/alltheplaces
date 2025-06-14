import json

from scrapy.spiders import Spider

from locations.items import Feature


class BurgermeDESpider(Spider):
    name = "burgerme_de"
    item_attributes = {"brand": "burgerme", "brand_wikidata": "Q108866856"}
    start_urls = ["https://www.burgerme.de/"]

    def parse(self, response, **kwargs):
        store_data_json = response.xpath('//script[@id="storelocator_new-js-extra"]').re_first(
            r"var storelocator\s*=\s*({.*});"
        )
        # GeoJSON as quoted string
        store_geojson = json.loads(json.loads(store_data_json)["stores"])

        properties_map = {
            "ref": "id",
            "name": "name",
            "street_address": "address",
            "postcode": "plz",
            "city": "city",
            "website": "permalink",
        }
        # Non-standard GeoJSON
        for feature in store_geojson["features"].values():
            properties = {k: feature["properties"][v] for k, v in properties_map.items()}
            properties["lon"] = feature["geometry"]["coordinates"][0]
            properties["lat"] = feature["geometry"]["coordinates"][1]
            yield Feature(properties)
