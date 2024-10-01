from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaGTSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_gt"
    region_code = "GT"
    dpz_market = "GUATEMALA"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
