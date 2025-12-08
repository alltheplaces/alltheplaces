from locations.storefinders.go_review_api import GoReviewApiSpider


class MaxisZASpider(GoReviewApiSpider):
    name = "maxis_za"
    domain = "maxislocal.localpages.io"
    item_attributes = {"brand": "Maxi's", "brand_wikidata": "Q116619188"}

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
