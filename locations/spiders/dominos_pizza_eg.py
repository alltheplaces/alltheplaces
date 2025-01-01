from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaEGSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_eg"
    region_code = "EG"
    dpz_market = "EGYPT"

    def post_process_item(self, item, response, location):
        if language_location := location.get("LanguageLocationInfo"):
            if ar_addr := language_location.get("ar"):
                item["street_address"] = ar_addr
                item["extras"]["addr:full:en"] = location["LocationInfo"]
                item["extras"]["addr:full:ar"] = item["addr_full"]
            else:
                item["street_address"] = location["LocationInfo"]
        if branch_ar := item["extras"].get("branch:ar"):
            item["branch"] = branch_ar
        yield item
