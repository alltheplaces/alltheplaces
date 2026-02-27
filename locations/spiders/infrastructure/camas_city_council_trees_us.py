from locations.storefinders.treeplotter import TreePlotterSpider


class CamasCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "camas_city_council_trees_us"
    item_attributes = {"operator": "Camas City Council", "operator_wikidata": "Q137825981", "state": "WA"}
    folder = "CamasWA"
    layer_name = "trees"
