from locations.storefinders.treeplotter import TreePlotterSpider


class TroyCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "troy_city_council_trees_us"
    item_attributes = {"operator": "Troy City Council", "operator_wikidata": "Q137825923", "state": "NY"}
    folder = "TroyNY"
    layer_name = "trees"
