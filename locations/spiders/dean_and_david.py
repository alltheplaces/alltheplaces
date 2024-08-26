from locations.storefinders.wp_go_maps import WpGoMapsSpider


class DeanAndDavidSpider(WpGoMapsSpider):
    name = "dean_and_david"
    item_attributes = {
        "brand_wikidata": "Q66132404",
        "brand": "dean&david",
    }
    allowed_domains = [
        "deananddavid.com",
    ]
