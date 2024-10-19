from locations.storefinders.go_review import GoReviewSpider


class EconoFoodsZASpider(GoReviewSpider):
    name = "econo_foods_za"
    item_attributes = {
        "brand": "Econo Foods",
        "brand_wikidata": "Q130406968",
    }
    start_urls = ["https://econoinfo.goreview.co.za/store-locator"]
