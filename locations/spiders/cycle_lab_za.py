import chompjs
from scrapy import Spider

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

    def parse(self, response):
        locations = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var markers = ")]/text()').get().split("var markers =")[1]
        )
        for location in locations:
            item = Feature()

            item["branch"] = location[0].replace(self.item_attributes["brand"], "").strip()
            item["lat"] = location[1]
            item["lon"] = location[2]

            info = response.xpath('//div[@class="Store-Location"][.//h3[text()="' + location[0] + '"]]')

            item["addr_full"] = clean_address(
                info.xpath('.//div[@class="Store-Location-Address"]/div/div/p/text()').getall()
            )
            item["phone"] = info.xpath('.//div[@class="number"]/h3/text()').get()

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(info.xpath('string(.//div[@class="hours-location"])').get())

            yield from self.post_process_item(item, response, location)

    def post_process_item(self, item, response, location):
        yield item
