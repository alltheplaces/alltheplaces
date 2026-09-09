from locations.storefinders.go_review import GoReviewSpider


class MooMooZASpider(GoReviewSpider):
    name = "moo_moo_za"
    item_attributes = {"brand": "Moo Moo Meet & Whine", "brand_wikidata": "Q130378128"}
    start_urls = ["https://moomoo.goreview.co.za/"]

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Moo Moo ", "")
        yield item
