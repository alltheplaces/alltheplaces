from locations.storefinders.wp_go_maps import WpGoMapsSpider


class TelepizzaSpider(WpGoMapsSpider):
    name = "telepizza"
    item_attributes = {
        "brand_wikidata": "Q2699863",
        "brand": "Telepizza",
    }
    allowed_domains = [
        "www.fooddeliverybrands.com",
    ]
