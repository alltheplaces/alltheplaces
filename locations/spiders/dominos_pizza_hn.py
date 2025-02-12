from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaHNSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_hn"
    region_code = "HN"
    dpz_market = "HONDURAS"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
