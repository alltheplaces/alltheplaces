from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BurgermeisterDESpider(WpGoMapsSpider):
    name = "burgermeister_de"
    item_attributes = {"brand": "Burgermeister", "brand_wikidata": "Q116382535"}
    allowed_domains = ["burgermeister.com"]
