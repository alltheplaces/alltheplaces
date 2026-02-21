from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.storefinders.treeplotter import TreePlotterSpider


class TrinityCollegeHartfordTreesUSSpider(TreePlotterSpider):
    name = "trinity_college_hartford_trees_us"
    item_attributes = {"operator": "Trinity College", "operator_wikidata": "Q1927705", "state": "CT"}
    folder = "TrinityCollege"
    layer_name = "trees"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if extras := item.get("extras"):
            if taxon_en := extras.get("taxon:en"):
                if taxon_en.upper() == "PARK BENCH":
                    return
        yield item
