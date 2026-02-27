from locations.storefinders.treeplotter import TreePlotterSpider


class SchenectadyCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "schenectady_city_council_trees_us"
    item_attributes = {"operator": "Schenectady City Council", "operator_wikidata": "Q137827192", "state": "NY"}
    folder = "SchenectadyNY"
    layer_name = "trees"
