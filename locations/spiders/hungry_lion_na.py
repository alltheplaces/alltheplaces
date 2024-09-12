from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.go_review import GoReviewSpider


class HungryLionNASpider(GoReviewSpider):
    name = "hungry_lion_na"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    start_urls = ["https://hlninfo.goreview.co.za/store-locator"]
