from locations.storefinders.forestree import ForestreeSpider


class WollondillyShireCouncilTreesAU(ForestreeSpider):
    name = "wollondilly_shire_council_trees_au"
    item_attributes = {"operator": "Wollondilly Shire Council", "operator_wikidata": "Q133836660", "state": "NSW"}
    host = "dev.forestree.studio"
    customer_id = "wollondilly"
