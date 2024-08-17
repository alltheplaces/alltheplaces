from locations.storefinders.uberall import UberallSpider


class SpaceNKGBSpider(UberallSpider):
    name = "space_nk_gb"
    item_attributes = {
        "brand_wikidata": "Q7572184",
        "brand": "Space NK",
    }
    key = "bdwTQJoL7hB55B0EimfSmXjiMRV8eg"
