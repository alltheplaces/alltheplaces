from locations.storefinders.go_review_api import GoReviewApiSpider


class GalitosZASpider(GoReviewApiSpider):
    name = "galitos_za"
    item_attributes = {"brand": "Galito's", "brand_wikidata": "Q116619555"}
    domain = "localpages.galitos.co.za"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        # Attributes not handled: "Can Trade Off Power Grid", "Dine-in", "Kerbside pickup"
        # See also GoReviewApiSpider itself
        yield item
