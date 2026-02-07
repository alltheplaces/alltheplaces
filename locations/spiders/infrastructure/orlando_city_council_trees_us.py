from locations.storefinders.treeplotter import TreePlotterSpider


class OrlandoCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "orlando_city_council_trees_us"
    item_attributes = {"operator": "Orlando City Council", "operator_wikidata": "Q137827399", "state": "FL"}
    folder = "OrlandoFL"
    layer_name = "trees"
