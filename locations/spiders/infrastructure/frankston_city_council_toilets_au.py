from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.flatgeobuf_spider import FlatGeobufSpider


class FrankstonCityCouncilToiletsAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_toilets_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "state": "VIC", "nsi_id": "N/A"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Public_Toilet.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["Facility_Name"]
        apply_category(Categories.TOILETS, item)
        if feature.get("Facility_Occupier") in ["FCC", "Public"]:
            apply_category({"access": "yes"}, item)
        elif feature.get("Facility_Occupier") == "Club/Org":
            apply_category({"access": "customers"}, item)
        apply_category({"fee": "no"}, item)
        yield item
