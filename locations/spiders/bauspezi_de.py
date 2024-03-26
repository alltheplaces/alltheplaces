from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BauSpeziDESpider(WpGoMapsSpider):
    name = "bauspezi_de"
    item_attributes = {
        "brand_wikidata": "Q85324366",
        "brand": "BauSpezi",
    }
    allowed_domains = ["bauspezi.de"]
