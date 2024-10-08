from scrapy import Request
from scrapy.linkextractors import LinkExtractor

from locations.storefinders.go_review import GoReviewSpider


class MooMooZASpider(GoReviewSpider):
    name = "moo_moo_za"
    item_attributes = {"brand": "Moo Moo Meet & Whine", "brand_wikidata": "Q130378128"}
    start_urls = ["https://moomoo.goreview.co.za/"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_store)

    def fetch_store(self, response):
        links = LinkExtractor(allow=r"^https:\/\/.+\.goreview\.co\.za\/goreview\/default$").extract_links(response)
        for link in links:
            store_page_url = link.url.replace("goreview.co.za/goreview/default", "goreview.co.za/store-information")
            yield Request(url=store_page_url, callback=self.parse)

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Moo Moo ", "")
        yield item
