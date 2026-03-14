from locations.storefinders.forestree import ForestreeSpider


class CityOfWestTorrensTreesAU(ForestreeSpider):
    name = "city_of_west_torrens_trees_au"
    item_attributes = {"operator": "City of West Torrens", "operator_wikidata": "Q56477681", "state": "SA"}
    host = "urbanforest.westtorrens.sa.gov.au"
    customer_id = "wt"
