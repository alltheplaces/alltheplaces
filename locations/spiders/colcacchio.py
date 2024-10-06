from scrapy import Request
from scrapy.linkextractors import LinkExtractor

from locations.storefinders.go_review import GoReviewSpider


class ColcacchioSpider(GoReviewSpider):
    name = "colcacchio"
    item_attributes = {"brand": "Col'Cacchio Pizzeria", "brand_wikidata": "Q25613087"}
    start_urls = ["https://colcacchio.goreview.co.za/"]
    skip_auto_cc_domain = True

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_store)

    def fetch_store(self, response):
        links = LinkExtractor(allow=r"^https:\/\/.+\.goreview\.co\.za\/goreview\/default$").extract_links(response)
        for link in links:
            store_page_url = link.url.replace("goreview.co.za/goreview/default", "goreview.co.za/store-information")
            yield Request(url=store_page_url, callback=self.parse)

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Col'Cacchio ", "")
        yield item
