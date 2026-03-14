from locations.storefinders.forestree import ForestreeSpider


class CityOfMitchamTreesAU(ForestreeSpider):
    name = "city_of_mitcham_trees_au"
    item_attributes = {"operator": "City of Mitcham", "operator_wikidata": "Q56477709", "state": "SA"}
    host = "dev.forestree.studio"
    customer_id = "mitcham"
