from locations.storefinders.rio_seo import RioSeoSpider


class BeallsRioUSSpider(RioSeoSpider):
    name = "bealls_us"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    domain = "stores.bealls.com"
