from locations.spiders.la_comer_mx import LaComerMXSpider


class FreskoMXSpider(LaComerMXSpider):
    name = "fresko_mx"
    item_attributes = {"brand": "Fresko", "brand_wikidata": "Q123943865"}
    locations_key = ["listFresko"]
