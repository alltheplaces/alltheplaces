from locations.storefinders.treeplotter import TreePlotterSpider


class TampaCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "tampa_city_council_trees_us"
    item_attributes = {"operator": "Tampa City Council", "operator_wikidata": "Q7681704", "state": "FL"}
    folder = "TampaFL"
    layer_name = "trees"
