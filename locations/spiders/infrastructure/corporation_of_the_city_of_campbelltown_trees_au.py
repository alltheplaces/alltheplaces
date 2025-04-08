from locations.storefinders.forestree import ForestreeSpider


class CorporationOfTheCityOfCampbelltownTreesAU(ForestreeSpider):
    name = "corporation_of_the_city_of_campbelltown_trees_au"
    item_attributes = {"operator": "Corporation of the City of Campbelltown", "operator_wikidata": "Q56477705", "state": "SA"}
    host = "dev.forestree.studio"
    customer_id = "ccc"
