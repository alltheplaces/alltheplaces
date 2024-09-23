from typing import Iterable

from scrapy import Request, Selector
from scrapy.http import Response

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class PaddyPallinAUSpider(AmastyStoreLocatorSpider):
    name = "paddy_pallin_au"
    item_attributes = {
        "brand": "Paddy Pallin",
        "brand_wikidata": "Q117949623",
        "extras": Categories.SHOP_SPORTS.value,
    }
    allowed_domains = ["www.paddypallin.com.au"]

    def start_requests(self) -> Iterable[Request]:
        # The request won't work without the headers supplied below.
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.paddypallin.com.au",
        }
        for domain in self.allowed_domains:
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers=headers)

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Request]:
        item["image"] = popup_html.xpath('//div[contains(@class, "amlocator-image")]/img/@src').get()
        address_fields = list(
            filter(
                lambda field: field.strip(),
                popup_html.xpath('//div[contains(@class, "amlocator-info-popup")]/text()').getall(),
            )
        )
        item["city"] = address_fields[0].strip().replace("City: ", "")
        item["postcode"] = address_fields[1].strip().replace("Zip: ", "")
        item["addr_full"] = address_fields[2].strip().replace("Address: ", "")
        item["state"] = address_fields[3].strip().replace("State: ", "")
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        if response.xpath('//div[contains(@class, "amlocator-location-info")]').get():
            item["email"] = (
                response.xpath(
                    '//div[contains(@class, "amlocator-location-info")]//a[contains(@href, "mailto:")]/text()'
                )
                .get()
                .strip()
            )
            item["phone"] = (
                response.xpath('//div[contains(@class, "amlocator-location-info")]//a[contains(@href, "tel:")]/text()')
                .get()
                .strip()
            )
            hours_string = " ".join(
                filter(None, response.xpath('//div[contains(@class, "amlocator-schedule-table")]//text()').getall())
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
