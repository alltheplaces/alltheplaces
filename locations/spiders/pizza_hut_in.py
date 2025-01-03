from locations.spiders.pizza_hut_gb import PizzaHutGBSpider


class PizzaHutINSpider(PizzaHutGBSpider):
    name = "pizza_hut_in"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://api.pizzahut.io/v1/huts?sectors=in-1"]
