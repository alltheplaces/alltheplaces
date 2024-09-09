from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BurgermeisterDESpider(WpGoMapsSpider):
    name = "burgermeister_de"
    item_attributes = {
        "brand_wikidata": "Q116382535",
        "brand": "Burgermeister",
    }
    allowed_domains = [
        "burgermeister.com",
    ]
