from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.treeplotter import TreePlotterSpider


class GawlerTownCouncilTreesAUSpider(TreePlotterSpider):
    name = "gawler_town_council_trees_au"
    item_attributes = {"operator": "Corporation of the Town of Gawler", "operator_wikidata": "Q56477731", "state": "SA"}
    host = "au.pg-cloud.com"
    folder = "GawlerCouncil"
    layer_name = "trees"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["extras"]["protected"] = "yes"
        yield item
