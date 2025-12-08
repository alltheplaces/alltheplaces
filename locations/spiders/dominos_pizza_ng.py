from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaNGSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ng"
    region_code = "NG"
    dpz_market = "NIGERIA"

    def post_process_item(self, item, response, location):
        if item["state"] == "NG":
            item.pop("state")
        yield item
