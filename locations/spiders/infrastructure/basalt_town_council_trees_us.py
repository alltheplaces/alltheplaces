from locations.storefinders.treeplotter import TreePlotterSpider


class BasaltTownCouncilTreesUSSpider(TreePlotterSpider):
    name = "basalt_town_council_trees_us"
    item_attributes = {"operator": "Basalt Town Council", "operator_wikidata": "Q137826387", "state": "CO"}
    folder = "basaltco"
    layer_name = "trees"
