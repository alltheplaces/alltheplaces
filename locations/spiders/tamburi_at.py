from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class TamburiATSpider(Spider):
    name = "tamburi_at"
    item_attributes = {"brand": "Tamburi", "brand_wikidata": "Q125176523"}
    start_urls = ["https://api.tamburi.at/api/remote_location/b2c"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["locationId"]
            item["lat"] = location["coordinateX"]
            item["lon"] = location["coordinateY"]
            item["branch"] = location["locationName"]
            item["housenumber"] = location["number"]
            item["street"] = location["street"]
            item["city"] = location["cityName"]
            item["postcode"] = location["zipCode"]

            yield item
