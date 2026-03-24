from locations.storefinders.wp_go_maps import WpGoMapsSpider


class OriginalTommysSpider(WpGoMapsSpider):
    name = "original_tommys"
    item_attributes = {"brand": "Original Tommy's", "brand_wikidata": "Q7102588"}
    allowed_domains = ["originaltommys.com"]
