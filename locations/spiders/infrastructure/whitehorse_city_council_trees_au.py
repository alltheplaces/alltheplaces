from locations.storefinders.forestree import ForestreeSpider


class WhitehorseCityCouncilTreesAU(ForestreeSpider):
    name = "whitehorse_city_council_trees_au"
    item_attributes = {"operator": "Whitehorse City Council", "operator_wikidata": "Q56477787", "state": "VIC"}
    host = "trees.whitehorse.vic.gov.au"
    customer_id = "wh"
