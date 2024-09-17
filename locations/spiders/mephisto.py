from typing import Iterable

from scrapy import Request, Selector
from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class MephistoSpider(AmastyStoreLocatorSpider):
    name = "mephisto"
    item_attributes = {"brand": "Mephisto", "brand_wikidata": "Q822975"}
    start_urls = ["https://www.mephisto.com/be-fr/points-de-vente/"]

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_website)

    def parse_website(self, response: Response) -> Iterable[Request]:
        page = "https://www.mephisto.com/be-fr/amlocator/index/ajax/"
        count_page = int(response.xpath('//*[@id="am-page-count"]/text()').get())
        for p in range(1, count_page + 1):
            yield Request(url=page + f"?p={p}", callback=self.parse)

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        # We don't want resellers. Only brand shop.
        if item["name"] in ("MEPHISTO-SHOP", "MEPHISTO SHOP"):
            item["street_address"] = item["addr_full"]
            item["addr_full"] = f"{item['addr_full']}, {item['postcode']} {item['city']}"
            yield item
