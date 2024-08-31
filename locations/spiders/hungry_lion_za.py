from locations.storefinders.go_review import GoReviewSpider


class HungryLionZASpider(GoReviewSpider):
    name = "hungry_lion_za"
    item_attributes = {"brand": "Hungry Lion", "brand_wikidata": "Q115636930"}
    start_urls = ["https://hlinfo.goreview.co.za/store-locator"]
