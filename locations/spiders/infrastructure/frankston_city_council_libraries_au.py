from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.flatgeobuf_spider import FlatGeobufSpider


class FrankstonCityCouncilLibrariesAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_libraries_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "state": "VIC", "nsi_id": "N/A"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Library.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = feature.get("Opening Hours")
        apply_category(Categories.LIBRARY, item)
        yield item
