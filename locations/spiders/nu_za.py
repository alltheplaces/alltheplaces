from scrapy import Request
from scrapy.linkextractors import LinkExtractor

from locations.storefinders.go_review import GoReviewSpider


class NuZASpider(GoReviewSpider):
    name = "nu_za"
    item_attributes = {
        "brand": "Nü",
        "brand_wikidata": "Q130400175",
    }
    start_urls = ["https://nu.goreview.co.za/store-locator/"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_store)

    def fetch_store(self, response):
        links = LinkExtractor(allow=r"^https:\/\/.+\.goreview\.co\.za\/goreview\/default$").extract_links(response)
        for link in links:
            store_page_url = link.url.replace("goreview.co.za/goreview/default", "goreview.co.za/store-information")
            yield Request(url=store_page_url, callback=self.parse)

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("Nü Health Food ", "")
        item["name"] = self.item_attributes["brand"]
        yield item
