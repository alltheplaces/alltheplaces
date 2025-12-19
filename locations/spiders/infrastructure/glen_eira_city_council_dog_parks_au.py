from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlenEiraCityCouncilDogParksAUSpider(JSONBlobSpider):
    name = "glen_eira_city_council_dog_parks_au"
    item_attributes = {"operator": "Glen Eira City Council", "operator_wikidata": "Q56477767", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/gleneira/public/DogParks_points.json"]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["name"] = feature["Park"]
        apply_category(Categories.LEISURE_DOG_PARK, item)
        yield item
