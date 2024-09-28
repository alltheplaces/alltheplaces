from locations.storefinders.go_review_api import GoReviewApiSpider


class SimplyAsiaZASpider(GoReviewApiSpider):
    name = "simply_asia_za"
    domain = "localpages.simplyasia.co.za"
    item_attributes = {"brand": "Simply Asia", "brand_wikidata": "Q130358521"}

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
