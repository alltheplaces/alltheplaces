from locations.storefinders.wp_go_maps import WpGoMapsSpider


class MochachosZASpider(WpGoMapsSpider):
    name = "mochachos_za"
    item_attributes = {
        "brand_wikidata": "Q116619117",
        "brand": "Mochachos",
    }
    allowed_domains = [
        "www.mochachos.com",
    ]
