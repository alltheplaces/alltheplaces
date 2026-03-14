from locations.storefinders.wp_go_maps import WpGoMapsSpider


class MenchiesSpider(WpGoMapsSpider):
    name = "menchies"
    allowed_domains = ["www.menchies.com"]
    item_attributes = {"brand": "Menchie's", "brand_wikidata": "Q6816528"}
