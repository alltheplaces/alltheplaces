from locations.storefinders.go_review import GoReviewSpider

HUNGRY_LION_SHARED_ATTRIBUTES = {"brand": "Hungry Lion", "brand_wikidata": "Q115636930"}


class HungryLionZASpider(GoReviewSpider):
    name = "hungry_lion_za"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    start_urls = ["https://hlinfo.goreview.co.za/store-locator"]
