from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.flatgeobuf_spider import FlatGeobufSpider


class FrankstonCityCouncilMensShedsAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_mens_sheds_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "state": "VIC", "nsi_id": "N/A"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Mens_Shed.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = feature.get("Click for More Information")
        if hours_string := feature.get("Opening Hours"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.COMMUNITY_CENTRE, item)
        apply_category({"community_centre:for", "man"}, item)
        yield item
