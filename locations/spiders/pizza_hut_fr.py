from locations.spiders.pizza_hut_gb import PIZZA_HUT, PizzaHutGBSpider


class PizzaHutFRSpider(PizzaHutGBSpider):
    name = "pizza_hut_fr"
    start_urls = ["https://api.pizzahut.io/v1/huts/?sector=fr-1"]
