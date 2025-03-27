from locations.storefinders.treeplotter import TreePlotterSpider


class LaneCoveCouncilTreesAUSpider(TreePlotterSpider):
    name = "lane_cove_council_trees_au"
    item_attributes = {"operator": "Lane Cove Council", "operator_wikidata": "Q56477512", "state": "NSW"}
    host = "au.pg-cloud.com"
    folder = "LaneCoveNSW"
    layer_name = "trees"
