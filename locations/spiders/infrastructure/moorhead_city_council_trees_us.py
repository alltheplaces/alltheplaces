from locations.storefinders.treeplotter import TreePlotterSpider


class MoorheadCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "moorhead_city_council_trees_us"
    item_attributes = {"operator": "Moorhead City Council", "operator_wikidata": "Q137826690", "state": "MN"}
    folder = "Moorhead"
    layer_name = "trees"
