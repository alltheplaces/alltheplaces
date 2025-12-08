from locations.storefinders.go_review_api import GoReviewApiSpider


class BargainBooksZASpider(GoReviewApiSpider):
    name = "bargain_books_za"
    item_attributes = {"brand": "Bargain Books", "brand_wikidata": "Q116741024"}
    domain = "bbpages.localpages.io"
