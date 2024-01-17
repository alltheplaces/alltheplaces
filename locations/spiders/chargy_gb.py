from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class ChargyGBSpider(Spider):
    name = "chargy_gb"
    item_attributes = {
        "brand": "char.gy",
        "brand_wikidata": "Q113465698",
        "country": "GB",
    }
    start_urls = ["https://char.gy/charge_points.geojson?bounds=48,-10,60.716907,2"]

    def parse(self, response):
        for charger in response.json()["features"]:
            item = Feature()

            item["lon"], item["lat"] = charger["geometry"]["coordinates"]

            item["ref"] = charger["properties"]["slug"]
            item["website"] = "https://char.gy/" + charger["properties"]["slug"]
            item["street_address"] = charger["properties"]["description"]
            item["postcode"] = charger["properties"]["postcode"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
