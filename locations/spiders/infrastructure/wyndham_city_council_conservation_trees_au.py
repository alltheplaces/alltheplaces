from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.treeplotter import TreePlotterSpider


class WyndhamCityCouncilConservationTreesAUSpider(TreePlotterSpider):
    name = "wyndham_city_council_conservation_trees_au"
    item_attributes = {"operator": "Wyndham City Council", "operator_wikidata": "Q96773743", "state": "VIC"}
    host = "au.pg-cloud.com"
    folder = "WyndhamCityCouncil"
    layer_name = "point_layer"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # Trees returned in this dataset appear to be council owned/operated
        # trees located in parks, nature reserves, roadside reserves
        # (different from nature strips with formal street tree plantings),
        # etc. There is a level of protection therefore provided by the
        # council.
        item["extras"]["protected"] = "yes"
        yield item
