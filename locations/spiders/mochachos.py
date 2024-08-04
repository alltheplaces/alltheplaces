from locations.storefinders.wp_go_maps import WpGoMapsSpider


class MochachosSpider(WpGoMapsSpider):
    name = "mochachos"
    item_attributes = {
        "brand_wikidata": "Q116619117",
        "brand": "Mochachos",
    }
    allowed_domains = [
        "www.mochachos.com",
    ]
