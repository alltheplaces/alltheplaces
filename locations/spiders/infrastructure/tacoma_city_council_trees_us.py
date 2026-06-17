from locations.storefinders.treeplotter import TreePlotterSpider


class TacomaCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "tacoma_city_council_trees_us"
    item_attributes = {"operator": "Tacoma City Council", "operator_wikidata": "Q137826482", "state": "WA"}
    folder = "TacomaWA"
    layer_name = "trees"
