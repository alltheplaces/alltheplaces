from locations.storefinders.go_review import GoReviewSpider

OCEAN_BASKET_SHARED_ATTRIBUTES = {"brand": "Ocean Basket", "brand_wikidata": "Q62075311"}


class OceanBasket1Spider(GoReviewSpider):
    name = "ocean_basket_1"
    item_attributes = OCEAN_BASKET_SHARED_ATTRIBUTES
    start_urls = [
        "https://oceanbasket.goreview.co.za/store-locator",  # South Africa
        "https://obmau.goreview.co.za/store-locator",
        "https://obzambia.goreview.co.za/store-locator",
        "https://obzim.goreview.co.za/store-locator",
        "https://obnigeria.goreview.co.za/store-locator",
        "https://obbot1.goreview.co.za/store-locator",
        "https://obnamibia.goreview.co.za/store-locator",
        "https://obkenya.goreview.co.za/store-locator",
        # "https://obghana.goreview.co.za/store-locator", # No locations showing, included in ocean_basket_2 instead
        "https://obcyprus.goreview.co.za/store-locator",
        "https://obuk.goreview.co.za/store-locator",
        "https://obdubai.goreview.co.za/store-locator",
        "https://obkw.goreview.co.za/store-locator",
        "https://obqa.goreview.co.za/store-locator",
        "https://obmt.goreview.co.za/store-locator/goreview/default",
    ]
