from locations.storefinders.forestree import ForestreeSpider


class CityOfPlayfordTreesAU(ForestreeSpider):
    name = "city_of_playford_trees_au"
    item_attributes = {"operator": "City of Playford", "operator_wikidata": "Q56477751", "state": "SA"}
    host = "dev.forestree.studio"
    customer_id = "playford"
