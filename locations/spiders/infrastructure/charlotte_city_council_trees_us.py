from locations.storefinders.treeplotter import TreePlotterSpider


class CharlotteCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "charlotte_city_council_trees_us"
    item_attributes = {"operator": "Charlotte City Council", "operator_wikidata": "Q137827368", "state": "NC"}
    folder = "CharlotteNC"
    layer_name = "trees"
