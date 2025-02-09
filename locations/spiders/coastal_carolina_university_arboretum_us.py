from locations.storefinders.treeplotter import TreePlotterSpider


class CoastalCarolinaUniversityArboretumUSSpider(TreePlotterSpider):
    name = "coastal_carolina_university_arboretum_us"
    item_attributes = {"operator": "Coastal Carolina University", "operator_wikidata": "Q1104405", "state": "SC"}
    folder = "Coastal"
    layer_name = "trees"
