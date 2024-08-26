from typing import Iterable

from scrapy import Request, Selector
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class NickScaliFurnitureSpider(AmastyStoreLocatorSpider):
    name = "nick_scali_furniture"
    item_attributes = {"brand": "Nick Scali Furniture", "brand_wikidata": "Q17053453"}
    allowed_domains = ["www.nickscali.com.au", "www.nickscali.co.nz"]

    def start_requests(self) -> Iterable[Request]:
        for domain in self.allowed_domains:
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Origin": f"https://{domain}",
            }
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers=headers)

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Request]:
        item["addr_full"] = " ".join(
            (" ".join(popup_html.xpath('//div[contains(@class, "amlocator-info-popup")]/text()').getall())).split()
        )
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        hours_raw = (
            " ".join(response.xpath('//div[contains(@class, "amlocator-schedule-table")]/div/span/text()').getall())
            .replace(" - ", " ")
            .replace(" am", "AM")
            .replace(" pm", "PM")
        ).split()
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            item["opening_hours"].add_range(day[0], day[1], day[2], "%I:%M%p")
        yield item
