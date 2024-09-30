from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaBHSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_bh"
    region_code = "BH"
    dpz_market = "BAHRAIN"

    def post_process_item(self, item, response, location):
        if language_location := location.get("LanguageLocationInfo"):
            if ar_addr := location["LanguageLocationInfo"].get("ar"):
                item["addr_full"] = ar_addr
                item["extras"]["addr:full:en"] = location["LocationInfo"]
                item["extras"]["addr:full:ar"] = item["addr_full"]
            else:
                item["addr_full"] = location["LocationInfo"]
        if branch_ar := item["extras"].get("branch:ar"):
            item["branch"] = branch_ar
        yield item
