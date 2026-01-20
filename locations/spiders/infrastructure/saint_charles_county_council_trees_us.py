from locations.storefinders.treeplotter import TreePlotterSpider


class SaintCharlesCountyCouncilTreesUSSpider(TreePlotterSpider):
    name = "saint_charles_county_council_trees_us"
    item_attributes = {"operator": "Saint Charles County Council", "operator_wikidata": "Q137827233", "state": "MO"}
    folder = "St_Charles"
    layer_name = "trees"
