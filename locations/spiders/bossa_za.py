import re

from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from locations.storefinders.go_review import GoReviewSpider


class BossaZASpider(GoReviewSpider):
    name = "bossa_za"
    item_attributes = {"brand": "Bossa", "brand_wikidata": "Q130376269"}
    start_urls = ["https://bossa.co.za/restaurants/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/branches/.+"),
            callback="parse_restaurants",
        )
    ]

    def parse_restaurants(self, response):
        if booking_link := response.xpath('.//a[contains(@href, "goreview.co.za/gobookings")]/@href').get():
            store_page_url = re.sub(r"goreview\.co\.za.*$", "goreview.co.za/store-information", booking_link)
            yield Request(url=store_page_url, callback=self.parse, meta={"website": response.url})

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("BOSSA ", "")
        item["website"] = response.meta["website"]
        yield item
