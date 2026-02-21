from locations.storefinders.treeplotter import TreePlotterSpider


class HoustonParksAndRecreationDepartmentTreesUSSpider(TreePlotterSpider):
    name = "houston_parks_and_recreation_department_trees_us"
    item_attributes = {
        "operator": "Houston Parks and Recreation Department",
        "operator_wikidata": "Q115018877",
        "state": "TX",
    }
    folder = "HoustonTX"
    layer_name = "trees"
