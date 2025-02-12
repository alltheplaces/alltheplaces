from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.spiders.eathappy import EathappySpider


class YuzuDESpider(EathappySpider):
    name = "yuzu_de"
    item_attributes = {"brand": "Yuzu", "brand_wikidata": "Q130392622", "extras": Categories.FAST_FOOD.value}
    base_domain = "https://www.yuzu-food.com"
    countries = {
        "DE": {
            "url": "https://www.yuzu-food.com/standorte/",
            "day_names": DAYS_DE,
        },
    }
    ajax_post_id = 71123
