from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaPRSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_pr"
    region_code = "PR"
    dpz_market = "PUERTO_RICO"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES

    def post_process_item(self, item, response, location):
        if item.get("postcode") == "USA":
            item.pop("postcode")
        yield item
