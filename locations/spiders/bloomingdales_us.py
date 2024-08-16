from locations.storefinders.rio_seo import RioSeoSpider


class BloomingdalesUSSpider(RioSeoSpider):
    name = "bloomingdales_us"
    item_attributes = {"brand": "Bloomingdale's", "brand_wikidata": "Q283383"}
    end_point = "https://maps.stores.bloomingdales.com.prod.rioseo.com"
