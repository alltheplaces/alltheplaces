from locations.hours import DAYS_PT
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaBRSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_br"
    region_code = "BR"
    dpz_market = "BRAZIL"
    domain = "order.golo01.dominos.com"
    dpz_language = "pt"
    days = DAYS_PT
