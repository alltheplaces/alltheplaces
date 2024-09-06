from locations.storefinders.go_review import GoReviewSpider


class PieCityZASpider(GoReviewSpider):
    name = "pie_city_za"
    item_attributes = {"brand": "Pie City", "brand_wikidata": "Q116619195"}
    start_urls = ["https://pcsl.goreview.co.za/store-locator"]
