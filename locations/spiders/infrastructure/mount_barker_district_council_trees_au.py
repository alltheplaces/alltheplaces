from locations.storefinders.forestree import ForestreeSpider


class MountBarkerDistrictCouncilTreesAU(ForestreeSpider):
    name = "mount_barker_district_council_trees_au"
    item_attributes = {"operator": "Mount Barker District Council", "operator_wikidata": "Q133836626", "state": "SA"}
    host = "dev.forestree.studio"
    customer_id = "mb"
