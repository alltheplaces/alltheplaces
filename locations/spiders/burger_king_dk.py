from locations.spiders.burger_king_se import BurgerKingSESpider


class BurgerKingDKSpider(BurgerKingSESpider):
    name = "burger_king_dk"
    start_urls = [
        "https://bk-dk-ordering-api.azurewebsites.net/api/v2/restaurants?latitude=59.330311012767446&longitude=18.068330468145753&radius=99900000&top=100000"
    ]
    restaurants_url = "https://bk-dk-ordering-api.azurewebsites.net/api/v2/restaurants/"
    website_template = "https://burgerking.dk/restauranter/{slug}"
