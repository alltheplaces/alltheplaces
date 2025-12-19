from locations.storefinders.forestree import ForestreeSpider


class WellingtonShireCouncilTreesAU(ForestreeSpider):
    name = "wellington_shire_council_trees_au"
    item_attributes = {"operator": "Wellington Shire Council", "operator_wikidata": "Q133836540", "state": "VIC"}
    host = "trees.wellington.vic.gov.au"
    customer_id = "well"
