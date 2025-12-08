from chompjs import parse_js_object
from scrapy import Request

from locations.structured_data_spider import StructuredDataSpider


class SweetfrogUSSpider(StructuredDataSpider):
    name = "sweetfrog_us"
    item_attributes = {"brand": "sweetFrog", "brand_wikidata": "Q16952110"}
    allowed_domains = ["locator.kahalamgmt.com", "www.sweetfrog.com"]
    start_urls = ["https://locator.kahalamgmt.com/locator/index.php?mode=desktop&brand=38"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        locator_js_blob = response.xpath('//script[contains(text(), "Locator.stores[0] = ")]/text()').get()
        location_js_blobs = list(filter(lambda x: "Locator.stores" in x, locator_js_blob.splitlines()))
        locations = [parse_js_object(x.split(" = ", 1)[1]) for x in location_js_blobs]
        for location in locations:
            url = (
                "https://www.sweetfrog.com/stores/frozen-yogurt-"
                + location["cleanCity"]
                + "/"
                + str(location["StoreId"])
            )
            yield Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        yield item
