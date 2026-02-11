from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChangeGroupSpider(JSONBlobSpider):
    name = "change_group"
    item_attributes = {"brand": "Change Group", "brand_wikidata": "Q5071758"}
    start_urls = ["https://uk.changegroup.com/dam/changegroup-mdm/branches.json"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("Forex"))
        feature.update(feature.pop("Localizacion")[0])

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["codBranch"]
        item["street_address"] = feature["direccion1"]
        item["postcode"] = feature["codPostal"]
        yield item
