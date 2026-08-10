from locations.storefinders.treeplotter import TreePlotterSpider


class DuluthCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "duluth_city_council_trees_us"
    item_attributes = {"operator": "Duluth City Council", "operator_wikidata": "Q5313500", "state": "MN"}
    folder = "DuluthMN"
    layer_name = "trees"
