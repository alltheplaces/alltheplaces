from locations.storefinders.forestree import ForestreeSpider


class CorporationOfTheCityOfUnleyTreesAU(ForestreeSpider):
    name = "corporation_of_the_city_of_unley_trees_au"
    item_attributes = {"operator": "Corporation of the City of Unley", "operator_wikidata": "Q56477727", "state": "SA"}
    host = "urbanforest.unley.sa.gov.au"
    customer_id = "cou"
