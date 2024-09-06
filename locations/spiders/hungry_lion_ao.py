from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.go_review import GoReviewSpider


class HungryLionAOSpider(GoReviewSpider):
    name = "hungry_lion_ao"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    start_urls = ["https://hlainfo.goreview.co.za/store-locator"]
