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
        locations = parse_js_object(
            response.xpath('//script[contains(text(), "var markers = ")]/text()').get().split("var markers =")[1]
        )
        # Coordinates are completely invalid however Google Maps street view
        # confirms the address was correct in 2022. Google Maps location
        # reviews indicate the shop is still trading in early 2025.
        if len(locations) != 1:
            raise RuntimeError(
                "This chain used to have more than one location and shared the same spider as parent brand with spider cycle_lab_za. Then it reduced to one location and the store locator page is no longer the same as cycle_lab_za. This new store locator page and this spider only supports a single location being returned. It appears though that this chain has expanded again to have more than one store. This spider thus needs to be rewritten."
            )
        properties = {
            "branch": locations[0][0],
            "addr_full": merge_address_lines(
                response.xpath('//div[@class="Store-Location-Address"]/div[1]/div[1]/p//text()').getall()
            ),
            "phone": response.xpath(
                '//div[@class="Store-Location-Address"]/div[1]/div[1]/div[@class="number"]/h3/text()'
            ).get(),
            "opening_hours": OpeningHours(),
        }
        hours_text = " ".join(response.xpath('//div[@class="hours-location"]//text()').getall()).replace(
            "Saturdays", "Saturday"
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)
        apply_category(Categories.SHOP_BICYCLE, properties)
        yield Feature(**properties)
