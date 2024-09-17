from locations.storefinders.wp_go_maps import WpGoMapsSpider


class TacoMayoUSSpider(WpGoMapsSpider):
    name = "taco_mayo_us"
    item_attributes = {
        "brand_wikidata": "Q2386946",
        "brand": "Taco Mayo",
    }
    allowed_domains = [
        "tacomayo.com",
    ]
