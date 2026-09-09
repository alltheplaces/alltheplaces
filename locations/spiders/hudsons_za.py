from locations.categories import Categories
from locations.storefinders.go_review import GoReviewSpider


class HudsonsZASpider(GoReviewSpider):
    name = "hudsons_za"
    item_attributes = {
        "brand": "Hudsons",
        "brand_wikidata": "Q130400275",
        "extras": Categories.RESTAURANT.value,
    }
    start_urls = ["https://hudsons.goreview.co.za/"]

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Hudsons ", "")
        item["name"] = self.item_attributes["brand"]
        yield item
