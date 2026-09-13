from typing import Any, Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BlueBikeBESpider(JSONBlobSpider):
    name = "blue_bike_be"
    item_attributes = {"brand_wikidata": "Q17332642"}
    start_urls = ["https://blue-bike.be/wp-json/bb/v1/locations"]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict[str, Any]) -> Iterable[Feature]:
        item.pop("state", None)
        if location["state"] != 1:
            return

        item["branch"] = item.pop("name")
        item["extras"]["capacity"] = str(location["capaciteit"])

        apply_category(
            Categories.BICYCLE_RENTAL_CARGO if location["soort"] == "bakfiets" else Categories.BICYCLE_RENTAL, item
        )
        if location["ebike"]:
            item["extras"]["rental"] = "city_bike;ebike"

        item["website"] = item["extras"]["website:nl"] = "https://blue-bike.be/locaties/#locatie={}".format(
            location["slug"]
        )
        item["extras"]["website:en"] = "https://blue-bike.be/en/locations/#locatie={}".format(location["slug"])
        item["extras"]["website:fr"] = "https://blue-bike.be/fr/emplacements/#locatie={}".format(location["slug"])

        yield item
