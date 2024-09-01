from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.go_review import GoReviewSpider


class HungryLionBWSpider(GoReviewSpider):
    name = "hungry_lion_bw"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    start_urls = ["https://hlbinfo.goreview.co.za/store-locator"]
