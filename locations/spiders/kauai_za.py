from locations.storefinders.go_review import GoReviewSpider


class KauaiZASpider(GoReviewSpider):
    name = "kauai_za"
    item_attributes = {"brand": "Kauai", "brand_wikidata": "Q116498799"}
    start_urls = ["https://kauai.goreview.co.za/store-locator"]

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("KAUAI ", "")
        yield item
