from locations.spiders.burger_king_ke import BurgerKingKESpider


class BurgerKingKESpider(BurgerKingKESpider):
    name = "burger_king_gh"
    start_urls = ["https://bk.uwapi.io/restaurants.html"]
    js_url = "https://bk.uwapi.io/js/googlemap.js"
