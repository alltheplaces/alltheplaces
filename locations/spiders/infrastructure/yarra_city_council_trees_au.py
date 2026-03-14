from locations.storefinders.forestree import ForestreeSpider


class YarraCityCouncilTreesAU(ForestreeSpider):
    name = "yarra_city_council_trees_au"
    item_attributes = {"operator": "Yarra City Council", "operator_wikidata": "Q28223935", "state": "VIC"}
    host = "trees.yarracity.vic.gov.au"
    customer_id = "yarra"
