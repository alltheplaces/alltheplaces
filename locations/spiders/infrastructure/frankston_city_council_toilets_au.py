from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.flatgeobuf_spider import FlatGeobufSpider
from locations.items import Feature


class FrankstonCityCouncilToiletsAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_toilets_au"
    item_attributes = {
        "operator": "Frankston City Council",
        "operator_wikidata": "Q132472668",
        "state": "VIC",
        "nsi_id": "N/A",
    }
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Public_Toilet.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["Facility_Name"]
        apply_category(Categories.TOILETS, item)
        match feature.get("Facility_Occupier"):
            case "FCC" | "Public":
                item["extras"]["access"] = "yes"
            case "Club/Org":
                item["extras"]["access"] = "customers"
            case _:
                self.logger.warning("Unknown public toilet access type: {}".format(feature.get("Facility_Occupier")))
        item["extras"]["fee"] = "no"
        yield item
