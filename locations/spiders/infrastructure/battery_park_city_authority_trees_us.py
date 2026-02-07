from locations.storefinders.treeplotter import TreePlotterSpider


class BatteryParkCityAuthorityTreesUSSpider(TreePlotterSpider):
    name = "battery_park_city_authority_trees_us"
    item_attributes = {"operator": "Battery Park City Authority", "operator_wikidata": "Q136565497", "state": "NY"}
    folder = "BPCA"
    layer_name = "trees"
