from locations.storefinders.go_review import GoReviewSpider


class TigerWheelAndTyreZASpider(GoReviewSpider):
    name = "tiger_wheel_and_tyre_za"
    item_attributes = {"brand": "Tiger Wheel & Tyre", "brand_wikidata": "Q120762656"}
    start_urls = ["https://twtinfo.goreview.co.za/store-locator"]
