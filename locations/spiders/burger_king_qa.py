from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingQASpider(Spider):
    name = "burger_king_qa"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerkingdelivery.qa/locate-us"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[contains(@class, "address-details")]'):
            item = Feature()
            item["ref"] = item["branch"] = location.xpath('.//*[contains(@class, "address-head")]/text()').get()
            item["addr_full"] = clean_address(location.xpath('.//*[@class="address"]//text()').getall()).removesuffix(
                " -"
            )
            item["phone"] = location.xpath('normalize-space(.//*[@class="phone-no"]/h6/text())').get()
            item["email"] = location.xpath('normalize-space(.//*[contains(@class, "email-id-name")]/text())').get()
            item["website"] = response.url
            extract_google_position(item, location)
            item["opening_hours"] = OpeningHours()
            days = location.xpath('.//*[contains(@class, "opening-days")]/text()').get()
            timing = " ".join(location.xpath('.//*[contains(@class, "hours-timing")]/text()').getall())
            item["opening_hours"].add_ranges_from_string(f"{days} {timing}")
            yield item
