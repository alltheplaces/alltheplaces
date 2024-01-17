from scrapy import Request

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class TedsCameraStoresAUSpider(AmastyStoreLocatorSpider):
    name = "teds_camera_stores_au"
    item_attributes = {
        "brand": "Ted's Camera Stores",
        "brand_wikidata": "Q117958394",
        "extras": {
            "shop": "camera",
        },
    }
    allowed_domains = ["www.teds.com.au"]

    def start_requests(self):
        # The request won't work without the headers supplied below.
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }
        for domain in self.allowed_domains:
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers=headers)

    def add_hours(self, response):
        item = response.meta["item"]
        if response.xpath('//div[contains(@class, "amlocator-location-info")]').get():
            item["email"] = (
                response.xpath('//div[contains(@class, "am-email")]/a[contains(@href, "mailto:")]/text()').get().strip()
            )
            item["phone"] = (
                response.xpath('//div[contains(@class, "am-phone")]/a[contains(@href, "tel:")]/text()').get().strip()
            )
            hours_string = " ".join(
                filter(None, response.xpath('//div[contains(@class, "amlocator-schedule-table")]//text()').getall())
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item

    def parse_item(self, item, location, popup_html):
        item["addr_full"] = ", ".join(
            filter(
                lambda field: field.strip(),
                popup_html.xpath('//div[contains(@class, "amlocator-info-popup")]/text()').getall(),
            )
        )
        yield Request(url=item["website"], meta={"item": item}, callback=self.add_hours)
