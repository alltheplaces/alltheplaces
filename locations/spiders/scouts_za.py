from chompjs import parse_js_object
from scrapy import Selector
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class ScoutsZASpider(JSONBlobSpider):
    name = "scouts_za"
    item_attributes = {
        "brand": "Scouts South Africa",
        "brand_wikidata": "Q7565791",
    }
    start_urls = ["https://www.scouts.org.za/scouts-near-you/"]
    allowed_domains = ["scouts.org.za"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_province)

    def parse_province(self, response):
        for link in LinkExtractor(allow=r"\/scouts-near-you\/$").extract_links(response):
            yield Request(url=link.url, callback=self.parse)

    def extract_json(self, response):
        data_raw = response.xpath('.//script[@id="gmw-map-js-extra"]/text()').get()
        return parse_js_object(data_raw.split('"locations":')[1])

    def post_process_item(self, item, response, location):
        apply_category(Categories.CLUB_SCOUT, item)
        selector = Selector(text=location["info_window_content"])
        item["name"] = selector.xpath('.//div[contains(@class, "title")]/a/text()').get()
        item["website"] = selector.xpath('.//div[contains(@class, "title")]/a/@href').get()
        item["addr_full"] = selector.xpath('.//div[contains(@class, "address")]/text()').get()
        yield item
