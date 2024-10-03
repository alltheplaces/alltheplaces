from scrapy import Request
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories
from locations.storefinders.go_review import GoReviewSpider


class CitiwoodZASpider(GoReviewSpider):
    name = "citiwood_za"
    item_attributes = {
        "brand": "Citiwood",
        "brand_wikidata": "Q130407139",
        "extras": Categories.SHOP_TRADE.value,
    }
    start_urls = ["https://citiwood.goreview.co.za/store-locator"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_store)

    def fetch_store(self, response):
        links = LinkExtractor(allow=r"^https:\/\/cw\d+\.goreview\.co\.za\/goreview\/default$").extract_links(response)
        for link in links:
            store_page_url = link.url.replace("goreview.co.za/goreview/default", "goreview.co.za/store-information")
            yield Request(url=store_page_url, callback=self.parse)

    def post_process_item(self, item, response):
        item["branch"] = item["branch"].replace("KAUAI ", "")
        yield item
