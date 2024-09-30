from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaAESpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ae"
    region_code = "AE"
    dpz_market = "UAE"
    additional_headers = {"Accept-Language": "en-GB"}  # To get the different languages

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
