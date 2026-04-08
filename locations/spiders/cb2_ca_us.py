import re
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Cb2CAUSSpider(StructuredDataSpider):
    name = "cb2_ca_us"
    item_attributes = {"brand": "CB2", "brand_wikidata": "Q113164236"}
    allowed_domains = ["www.cb2.com", "www.cb2.ca"]
    start_urls = ["https://www.cb2.com/stores/?viewIndex=storeList"]
    # Basic anti-bot detection and rate limiting in use.
    # Check for non-zero "downloader/response_status_count/403" stat.
    requires_proxy = True

    def parse(self, response: TextResponse) -> Iterable[Request]:
        # Parse the raw store list from a JavaScript blob as React is used
        # and dynamically renders the DOM from this JavaScript blob.
        store_list_js_blob = response.xpath(
            '//script[contains(text(), "React.createElement(CB2StoreList,")]/text()'
        ).get()
        store_list_js_blob = store_list_js_blob.split('"allStoreList":', 1)[1].split(',"storeListView":', 1)[0]
        store_list = parse_js_object(store_list_js_blob)
        for store in store_list:
            store_url = store["domainUrl"] + "/stores/" + store["seoName"] + "/str" + str(store["storeNumber"])
            yield Request(url=store_url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if m := re.search(r"^https:\/\/www\.cb2\.(?:com|ca)\/stores\/[^\/]+\/str(\d+)$", response.url):
            item["ref"] = m.group(1)
        apply_category(Categories.SHOP_FURNITURE, item)
        item.pop("facebook", None)
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix("CB2 Outlet at ").removeprefix("CB2 ")
        yield item
