from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class AvroraUASpider(Spider):
    name = "avrora_ua"
    item_attributes = {"brand": "Аврора", "brand_wikidata": "Q117669095"}
    start_urls = ["https://avrora.ua/index.php?dispatch=pwa.store_locations&is_ajax=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["objects"].values():
            item = Feature()
            item["ref"] = location["shopNumber"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["street_address"] = location["name"]
            item["city"] = location["city"]
            item["country"] = location["country"]
            item["website"] = "https://avrora.ua/index.php?dispatch=store_locator.view&store_location_id={}".format(
                location["shopNumber"]
            )

            yield item
