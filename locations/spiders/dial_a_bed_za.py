from html import unescape
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
        item["street_address"] = unescape(
            " ".join(popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall())
            .split("   Address:", 1)[1]
            .split("   ", 1)[0]
            .strip()
        )
        item["city"] = unescape(
            " ".join(popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall())
            .split("City:", 1)[1]
            .split("   ", 1)[0]
            .strip()
        )
        item["phone"] = unescape(
            " ".join(popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall())
            .split("   Phone:", 1)[1]
            .split("   ", 1)[0]
            .strip()
        )
        item["branch"] = item.pop("name").replace("Dial a Bed", "").strip()
        yield item
