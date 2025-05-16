from locations.storefinders.treeplotter import TreePlotterSpider


class BrockportVillageBoardTreesUSSpider(TreePlotterSpider):
    name = "brockport_village_board_trees_us"
    item_attributes = {"operator": "Brockport Village Board", "operator_wikidata": "Q132178943", "state": "NY"}
    folder = "brockportny"
    layer_name = "trees"
