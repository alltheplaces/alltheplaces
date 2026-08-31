from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ChrisWillemseCyclesZASpider(Spider):
    name = "chris_willemse_cycles_za"
    item_attributes = {"brand": "Chris Willemse Cycles", "brand_wikidata": "Q130488816"}
    allowed_domains = ["cwcycles.co.za"]
    start_urls = ["https://cwcycles.co.za/store-location"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        markers = parse_js_object(
            response.xpath('//script[contains(text(), "var markers = ")]/text()').get().split("var markers =")[1]
        )
        cards = response.xpath('//*[@class="Store-Location"]')
        for marker, card in zip(markers, cards):
            if not marker[0].startswith("CWC"):
                # The page also lists stores of the parent brand, captured by cycle_lab_za.
                continue
            item = Feature()
            item["branch"] = marker[0].removeprefix("CWC ")
            item["lat"], item["lon"] = marker[1], marker[2]
            item["addr_full"] = merge_address_lines(
                card.xpath('.//*[@class="Store-Location-Address"]//p/text()').getall()
            )
            item["phone"] = card.xpath('.//i[@class="fa fa-phone"]/../text()').get("").strip()
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                card.xpath('string(.//*[@class="hours-location"])').get("").replace("Saturdays", "Saturday")
            )
            apply_category(Categories.SHOP_BICYCLE, item)
            yield item
