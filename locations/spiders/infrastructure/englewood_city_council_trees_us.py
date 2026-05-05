from locations.storefinders.treeplotter import TreePlotterSpider


class EnglewoodCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "englewood_city_council_trees_us"
    item_attributes = {"operator": "Englewood City Council", "operator_wikidata": "Q138499485", "state": "CO"}
    folder = "Englewood"
    layer_name = "trees"
