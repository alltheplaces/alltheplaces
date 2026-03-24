from locations.storefinders.wp_go_maps import WpGoMapsSpider


class DeanAndDavidSpider(WpGoMapsSpider):
    name = "dean_and_david"
    item_attributes = {"brand": "dean&david", "brand_wikidata": "Q66132404"}
    allowed_domains = ["deananddavid.com"]
