from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.flatgeobuf_spider import FlatGeobufSpider


class FrankstonCityCouncilAquaticCentresAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_aquatic_centres_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "state": "VIC", "nsi_id": "N/A"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Recreation/Aquatic_Centre.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = feature.get("Click for More Information")
        apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
        apply_category({"access": "yes"}, item)
        apply_category({"sport": "swimming"}, item)
        yield item
