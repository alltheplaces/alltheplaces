from locations.categories import Categories
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class ChamasTacosFRSpider(WpGoMapsSpider):
    name = "chamas_tacos_fr"
    item_attributes = {"brand_wikidata": "Q127411207", "brand": "Chamas Tacos", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["chamas-tacos.com"]
