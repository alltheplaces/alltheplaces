from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BurgermeisterSpider(WpGoMapsSpider):
    name = "burgermeister"
    item_attributes = {
        "brand_wikidata": "Q116382535",
        "brand": "Burgermeister",
    }
    allowed_domains = [
        "burgermeister.com",
    ]
