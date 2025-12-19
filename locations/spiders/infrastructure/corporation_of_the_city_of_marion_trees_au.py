from locations.storefinders.forestree import ForestreeSpider


class CorporationOfTheCityOfMarionTreesAU(ForestreeSpider):
    name = "corporation_of_the_city_of_marion_trees_au"
    item_attributes = {"operator": "Corporation of the City of Marion", "operator_wikidata": "Q56477739", "state": "SA"}
    host = "trees.marion.sa.gov.au"
    customer_id = "com"
