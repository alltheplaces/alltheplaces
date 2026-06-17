from locations.storefinders.treeplotter import TreePlotterSpider


class ClosterBoroughCouncilTreesUSSpider(TreePlotterSpider):
    name = "closter_borough_council_trees_us"
    item_attributes = {"operator": "Closter Borough Council", "operator_wikidata": "Q137826266", "state": "NJ"}
    folder = "ClosterNJ"
    layer_name = "trees"
