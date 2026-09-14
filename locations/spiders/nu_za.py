from locations.storefinders.go_review import GoReviewSpider


class NuZASpider(GoReviewSpider):
    name = "nu_za"
    item_attributes = {"brand": "Nü Health Food", "brand_wikidata": "Q130400175"}
    start_urls = ["https://nu.goreview.co.za/store-locator/"]

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Nü Health Food ", "")
        item["name"] = self.item_attributes["brand"]
        yield item
