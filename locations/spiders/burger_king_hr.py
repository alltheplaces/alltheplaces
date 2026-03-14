import re
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingHRSpider(Spider):
    name = "burger_king_hr"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.hr/map.html"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in re.findall(
            r"iframe\.src\s*=\s*'(\w+\.html)';", response.xpath('//*[contains(text(),"markersData")]/text()').get()
        ):
            yield scrapy.Request(url="https://burgerking.hr/" + link, callback=self.parse_details)

    def parse_details(self, response):
        item = Feature()
        item["name"] = response.xpath("//h2/text()").get()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        if "bkrijeka" in response.url:
            item["street_address"] = response.xpath("//p[1]/text()").get()
            item["addr_full"] = item["addr_full"] = merge_address_lines(
                [item["street_address"], response.xpath("//p[3]/text()").get()]
            )
        else:

            item["street_address"] = response.xpath("//p[2]/text()").get()
            item["addr_full"] = merge_address_lines(
                [response.xpath("//p/text()").get(), item["street_address"], response.xpath("//p[3]/text()").get()]
            )

        apply_category(Categories.FAST_FOOD, item)
        properties = response.xpath('//*[@class="modal-list"]//*[@class="lista"]').xpath("normalize-space()").getall()
        apply_yes_no(Extras.WIFI, item, "Wifi" in properties)
        apply_yes_no(PaymentMethods.CARDS, item, "Kartično plaćanje" in properties)
        apply_yes_no(Extras.DELIVERY, item, "Dostava" in properties)

        yield item
