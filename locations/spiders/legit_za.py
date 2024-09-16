from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request

from locations.json_blob_spider import JSONBlobSpider


class LegitZASpider(JSONBlobSpider):
    name = "legit_za"
    start_urls = ["https://www.legit.co.za/pages/store-locator"]
    item_attributes = {"brand": "LEGiT", "brand_wikidata": "Q122959274"}

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_js)

    def fetch_js(self, response):
        urls = parse_js_object(
            response.xpath('.//script[contains(text(), "var urls =")]/text()').get().split("var urls =")[1]
        )
        js_url = [u for u in urls if "amaicdn.com/storelocator-prod/wtb/" in u]  # should be only one
        for url in js_url:
            yield JsonRequest(url=url, callback=self.parse)

    def extract_json(self, response):
        chunks = response.text.split("SCASLWtb=")
        return parse_js_object(chunks[1])["locations"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
