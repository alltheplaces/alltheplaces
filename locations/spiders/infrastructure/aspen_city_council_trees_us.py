from locations.storefinders.treeplotter import TreePlotterSpider


class AspenCityCouncilTreesUSSpider(TreePlotterSpider):
    name = "aspen_city_council_trees_us"
    item_attributes = {"operator": "Aspen City Council", "operator_wikidata": "Q137826078", "state": "CO"}
    folder = "Aspen"
    layer_name = "trees"
