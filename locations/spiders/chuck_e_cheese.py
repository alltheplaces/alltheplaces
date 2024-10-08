from locations.storefinders.rio_seo import RioSeoSpider


class ChuckECheeseSpider(RioSeoSpider):
    name = "chuck_e_cheese"
    item_attributes = {
        "brand_wikidata": "Q2438391",
        "brand": "Chuck E. Cheese",
    }
    end_point = "https://maps.locations.chuckecheese.com"
