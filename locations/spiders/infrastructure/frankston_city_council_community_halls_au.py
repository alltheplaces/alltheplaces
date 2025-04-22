from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.flatgeobuf_spider import FlatGeobufSpider
from locations.items import Feature


class FrankstonCityCouncilCommunityHallsAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_community_halls_au"
    item_attributes = {
        "operator": "Frankston City Council",
        "operator_wikidata": "Q132472668",
        "state": "VIC",
        "nsi_id": "N/A",
    }
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Community_Hall.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("phone", None)
        item["website"] = feature.get("Click for More Information")
        apply_category(Categories.COMMUNITY_CENTRE, item)
        yield item
