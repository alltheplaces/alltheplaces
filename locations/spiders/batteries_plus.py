from locations.storefinders.rio_seo import RioSeoSpider


class BatteriesPlusSpider(RioSeoSpider):
    name = "batteries_plus"
    item_attributes = {"brand": "Batteries Plus Bulbs", "brand_wikidata": "Q17005157"}
    end_point = "https://maps.stores.batteriesplus.com.prod.rioseo.com"
