from locations.storefinders.wordpress_heron_foods_spider import WordpressHeronFoodsSpider


class CeriseEtPotironFRSpider(WordpressHeronFoodsSpider):
    name = "cerise_et_potiron_fr"
    item_attributes = {"brand": "Cerise et Potiron", "brand_wikidata": "Q91634572"}
    domain = "www.cerise-et-potiron.fr"
    radius = 600
    lat = 45.7490921
    lon = 4.8419781
