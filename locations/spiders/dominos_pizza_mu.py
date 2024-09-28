from locations.storefinders.go_review import GoReviewSpider


class DominosPizzaMUSpider(GoReviewSpider):
    name = "dominos_pizza_mu"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://dominosmau.goreview.co.za/store-locator"]
