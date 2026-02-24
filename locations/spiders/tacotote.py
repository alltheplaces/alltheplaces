from locations.storefinders.wp_go_maps import WpGoMapsSpider


class TacototeSpider(WpGoMapsSpider):
    name = "tacotote"
    item_attributes = {"brand": "Tacotote", "brand_wikidata": "Q16992316"}
    allowed_domains = ["tacotote.com"]
