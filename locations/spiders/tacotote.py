from locations.categories import Categories
from locations.storefinders.wp_go_maps import WPGoMapsSpider


class TacototeSpider(WPGoMapsSpider):
    name = "tacotote"
    item_attributes = {
        "brand": "El Taco Tote",
        "brand_wikidata": "Q16992316",
        "extras": Categories.RESTAURANT.value,
    }
    allowed_domains = ["tacotote.com"]
