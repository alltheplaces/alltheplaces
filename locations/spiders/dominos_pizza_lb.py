from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaLBSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_lb"
    region_code = "LB"
    dpz_market = "LEBANON"

    def post_process_item(self, item, response, location):
        # Doing this instead of setting the language to ar so that opening hours parsing still works
        item["branch"] = item["extras"]["branch:ar"]
        yield item
