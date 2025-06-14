from locations.storefinders.treeplotter import TreePlotterSpider


class GrandviewHeightsCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "grandview_heights_city_council_trees_us"
    item_attributes = {"operator": "Grandview Heights City Council", "operator_wikidata": "Q132178903", "state": "OH"}
    folder = "GHPR"
    layer_name = "trees"
