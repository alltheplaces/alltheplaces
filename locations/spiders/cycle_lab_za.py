from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


# Also used by chris_willemse_cycles_za and the_pro_shop_za
class CycleLabZASpider(Spider):
    name = "cycle_lab_za"
    item_attributes = {
        "brand": "Cycle Lab",
        "brand_wikidata": "Q130487839",
    }
    start_urls = ["https://www.cyclelab.com/store"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="Store-Location-Content"]'):
            item = Feature()
            # Only addresses are available, no coordinates are there.
            item["addr_full"] = clean_address(
                location.xpath('.//*[@class="Store-Location-Address"]//p/text()').getall()
            )

            item["phone"] = location.xpath('.//i[@class="fa fa-phone"]/../text()').get("")
            item["email"] = location.xpath('.//i[@class="fa fa-envelope"]/../text()').get("")

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location.xpath('string(.//*[@class="hours-location"])').get())

            yield from self.post_process_item(item, response, location)

    def post_process_item(self, item: Feature, response: Response, location: Selector) -> Iterable[Feature]:
        yield item
