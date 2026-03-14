from locations.storefinders.treeplotter import TreePlotterSpider


class MerriBekCityCouncilTreesAUSpider(TreePlotterSpider):
    name = "merri_bek_city_council_trees_au"
    item_attributes = {"operator": "Merri-bek City Council", "operator_wikidata": "Q30267291", "state": "VIC"}
    host = "au.pg-cloud.com"
    folder = "Merri-bek"
    layer_name = "trees"
