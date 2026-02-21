from locations.storefinders.treeplotter import TreePlotterSpider


class ForeverBalboaParkTreesUSSpider(TreePlotterSpider):
    name = "forever_balboa_park_trees_us"
    item_attributes = {"operator": "Forever Balboa Park", "operator_wikidata": "Q137826817", "state": "CA"}
    folder = "SDTT"
    layer_name = "trees"
    organisation_id = 2
