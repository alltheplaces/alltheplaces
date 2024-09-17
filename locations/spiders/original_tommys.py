from locations.storefinders.wp_go_maps import WpGoMapsSpider


class OriginalTommysSpider(WpGoMapsSpider):
    name = "original_tommys"
    item_attributes = {
        "brand_wikidata": "Q7102588",
        "brand": "Original Tommy's",
    }
    allowed_domains = [
        "originaltommys.com",
    ]
