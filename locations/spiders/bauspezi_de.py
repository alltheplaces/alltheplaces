from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BauspeziDESpider(WpGoMapsSpider):
    name = "bauspezi_de"
    item_attributes = {"brand": "BauSpezi", "brand_wikidata": "Q85324366"}
    allowed_domains = ["bauspezi.de"]
