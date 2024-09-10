import chompjs
from scrapy import Selector
from scrapy.http import Request

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.sunglass_hut_1 import SUNGLASS_HUT_SHARED_ATTRIBUTES


class SunglassHutNAZASpider(JSONBlobSpider):
    name = "sunglass_hut_na_za"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    start_urls = ["https://za.sunglasshut.com/store-locator"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_js)

    def fetch_js(self, response):
        js_file = response.xpath('.//link[@rel="prefetch"][contains(@href, "/js/about")]/@href').get()
        yield Request(url="https://za.sunglasshut.com/" + js_file, callback=self.parse)

    def extract_json(self, response):
        return chompjs.parse_js_object(response.text.split("markers:")[1])

    def post_process_item(self, item, response, location):
        item["branch"] = location["store_title"].replace(self.item_attributes["brand"], "").strip()
        item.pop("name")
        item["addr_full"] = item["addr_full"].split("<br/>")[-1]
        item["phone"] = Selector(text=location["store_name"]).xpath('.//a[contains(@href, "tel")]/@href').get()
        yield item
