from locations.storefinders.storepoint import StorepointSpider


class BloomsTheChemistAUSpider(StorepointSpider):
    name = "blooms_the_chemist_au"
    item_attributes = {"brand": "Blooms The Chemist", "brand_wikidata": "Q63367543"}
    key = "15f056510a1d3a"
