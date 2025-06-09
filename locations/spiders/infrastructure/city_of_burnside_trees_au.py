from locations.storefinders.forestree import ForestreeSpider


class CityOfBurnsideTreesAU(ForestreeSpider):
    name = "city_of_burnside_trees_au"
    item_attributes = {"operator": "City of Burnside", "operator_wikidata": "Q56477701", "state": "SA"}
    host = "trees.burnside.sa.gov.au"
    customer_id = "cob"
