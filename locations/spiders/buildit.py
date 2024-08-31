import chompjs
from scrapy.http import JsonRequest, Request

from locations.json_blob_spider import JSONBlobSpider


class BuilditSpider(JSONBlobSpider):
    name = "buildit"
    item_attributes = {"brand": "Build it", "brand_wikidata": "Q116755810"}
    start_urls = ["https://www.buildit.co.za/"]
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.store_search)

    def store_search(self, response):
        queries = chompjs.parse_js_object(
            response.xpath('.//input[@name="p$lt$zoneHeader$NavStoreSelector$hidSuburbs"]/@value').get()
        )
        for query in queries:
            yield JsonRequest(
                url="https://www.buildit.co.za/api/Store/GetStoresByArea",
                data={"Suburb": query["Name"], "ProvinceId": query["ProvinceId"], "Services": []},
                method="POST",
                callback=self.parse,
            )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["website"] = f"https://www.buildit.co.za/Stores/View/{location['Alias']}"
        yield item
