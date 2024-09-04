from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.go_review import GoReviewSpider


class HungryLionZMSpider(GoReviewSpider):
    name = "hungry_lion_zm"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    start_urls = ["https://hlzinfo.goreview.co.za/store-locator"]
