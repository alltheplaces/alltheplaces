from locations.spiders.pizza_hut_gb import PizzaHutGBSpider


class PizzaHutFRSpider(PizzaHutGBSpider):
    name = "pizza_hut_fr"
    start_urls = ["https://api.pizzahut.io/v1/huts/?sector=fr-1"]
    PIZZA_HUT_DELIVERY = {"name": "Pizza Hut Delivery", "brand": "Pizza Hut", "brand_wikidata": "Q191615"}
