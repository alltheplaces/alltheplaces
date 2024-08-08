from scrapy import Request

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class NickScaliFurnitureSpider(AmastyStoreLocatorSpider):
    name = "nick_scali_furniture"
    item_attributes = {"brand": "Nick Scali Furniture", "brand_wikidata": "Q17053453"}
    allowed_domains = ["www.nickscali.com.au", "www.nickscali.co.nz"]

    def start_requests(self):
        for domain in self.allowed_domains:
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Origin": f"https://{domain}",
            }
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers=headers)

    def parse_item(self, item, location, popup_html):
        item["addr_full"] = " ".join(
            (" ".join(popup_html.xpath('//div[contains(@class, "amlocator-info-popup")]/text()').getall())).split()
        )
        yield Request(url=item["website"], meta={"item": item}, callback=self.add_hours)

    def add_hours(self, response):
        item = response.meta["item"]
        oh = OpeningHours()
        hours_raw = (
            " ".join(response.xpath('//div[contains(@class, "amlocator-schedule-table")]/div/span/text()').getall())
            .replace(" - ", " ")
            .replace(" am", "AM")
            .replace(" pm", "PM")
        ).split()
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            oh.add_range(day[0], day[1], day[2], "%I:%M%p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
