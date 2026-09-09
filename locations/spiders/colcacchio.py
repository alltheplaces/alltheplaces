from locations.storefinders.go_review import GoReviewSpider


class ColcacchioSpider(GoReviewSpider):
    name = "colcacchio"
    item_attributes = {"brand": "Col'Cacchio Pizzeria", "brand_wikidata": "Q25613087"}
    start_urls = ["https://colcacchio.goreview.co.za/"]
    skip_auto_cc_domain = True

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Col'Cacchio ", "")
        yield item
