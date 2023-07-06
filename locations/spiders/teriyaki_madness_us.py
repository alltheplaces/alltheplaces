from locations.storefinders.storerocket import StoreRocketSpider


class TeriyakiMadnessUSSpider(StoreRocketSpider):
    name = "teriyaki_madness_us"
    item_attributes = {"brand": "Teriyaki Madness", "brand_wikidata": "Q107692862"}
    storerocket_id = "aKpDeXV4dR"
