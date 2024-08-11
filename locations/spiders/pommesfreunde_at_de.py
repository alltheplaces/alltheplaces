from locations.storefinders.wp_go_maps import WpGoMapsSpider


class PommesfreundeATDESpider(WpGoMapsSpider):
    name = "pommesfreunde_at_de"
    item_attributes = {
        "brand_wikidata": "Q117083946",
        "brand": "Pommesfreunde",
    }
    allowed_domains = [
        "pommesfreunde.de",
    ]
