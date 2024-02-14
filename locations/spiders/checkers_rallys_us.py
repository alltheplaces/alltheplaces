from locations.storefinders.yext import YextSpider


class CheckersRallysUS(YextSpider):
    name = "checkers_rallys_us"
    api_key = "3a0695216a74763b09659ee6021687a0"
    wanted_types = ["restaurant"]
    # Data centre netblocks appear to be blocked.
    requires_proxy = True

    def parse_item(self, item, location):
        if "Checkers" in location["brands"]:
            item["brand"] = "Checkers"
            item["brand_wikidata"] = "Q63919315"
        elif "Rally's" in location["brands"]:
            item["brand"] = "Rally's"
            item["brand_wikidata"] = "Q63919323"
        else:
            self.logger.warning("Unknown brand: {}".format(location["brands"][0]))
            return
        item.pop("facebook", None)
        item.pop("twitter", None)
        item["extras"].pop("contact:instagram", None)
        yield item
