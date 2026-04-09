from locations.storefinders.treeplotter import TreePlotterSpider


class LeawooddCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "leawood_city_council_trees_us"
    item_attributes = {"operator": "Leawood City Council", "operator_wikidata": "Q138499296", "state": "KS"}
    folder = "leawood"
    layer_name = "trees"
