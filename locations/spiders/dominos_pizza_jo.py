from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaJOSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_jo"
    region_code = "JO"
    dpz_market = "JORDAN"

    def post_process_item(self, item, response, location):
        if branch_ar := item["extras"].get("branch:ar"):
            item["branch"] = branch_ar
        yield item
