from locations.storefinders.treeplotter import TreePlotterSpider


class CairnsRegionalCouncilTreesAUSpider(TreePlotterSpider):
    name = "cairns_regional_council_trees_au"
    item_attributes = {"operator": "Cairns Regional Council", "operator_wikidata": "Q85370939", "state": "QLD"}
    host = "au.pg-cloud.com"
    folder = "Cairns"
    layer_name = "trees"
