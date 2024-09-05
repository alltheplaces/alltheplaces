from typing import Iterable

from scrapy import Request, Selector

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class DialABedZASpider(AmastyStoreLocatorSpider):
    name = "dial_a_bed_za"
    item_attributes = {"brand": "Dial-a-Bed", "brand_wikidata": "Q116429178"}
    allowed_domains = ["www.dialabed.co.za"]

    def start_requests(self) -> Iterable[Request]:
        # The request won't work without the headers supplied below.
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }
        for domain in self.allowed_domains:
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers=headers)

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        for line in popup_html.xpath('.//div[@class="amlocator-info-popup"]/text()').getall():
            if line.strip().startswith("City:"):
                item["city"] = line.replace("City:", "").strip()
            elif line.strip().startswith("Postal Code:"):
                item["postcode"] = line.replace("Postal Code:", "").strip()
            elif line.strip().startswith("Address:"):
                item["street_address"] = line.replace("Address:", "").strip()
        if "city" in item and "street_address" in item:
            if item["city"] in item["street_address"]:
                item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").replace("Dial a Bed", "").strip()
        yield item
