from locations.storefinders.wp_go_maps import WpGoMapsSpider


class ChamasTacosFRSpider(WpGoMapsSpider):
    name = "chamas_tacos_fr"
    item_attributes = {"brand": "Chamas Tacos", "brand_wikidata": "Q127411207"}
    allowed_domains = ["chamas-tacos.com"]
