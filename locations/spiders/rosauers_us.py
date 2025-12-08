from locations.storefinders.wp_go_maps import WpGoMapsSpider


class RosauersUSSpider(WpGoMapsSpider):
    name = "rosauers_us"
    item_attributes = {"brand": "Rosauers", "brand_wikidata": "Q7367458"}
    allowed_domains = ["www.rosauers.com"]
    map_id = 1
