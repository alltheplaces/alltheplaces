from locations.storefinders.treeplotter import TreePlotterSpider


class ViennaTownCouncilTreesUSSpider(TreePlotterSpider):
    name = "vienna_town_council_trees_us"
    item_attributes = {"operator": "Vienna Town Council", "operator_wikidata": "Q137827272", "state": "VA"}
    folder = "ViennaVA"
    layer_name = "trees"
