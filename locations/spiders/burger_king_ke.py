from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Request

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingKESpider(Spider):
    name = "burger_king_ke"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.ke/restaurants.html"]
    js_url = "https://burgerking.ke/js/googlemap.js"
    coordinates = {}

    def start_requests(self):
        yield Request(url=self.js_url, callback=self.parse_coordinates)
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse)

    def parse_coordinates(self, response):
        for line in response.text.split("\n"):
            if line.startswith("const loc_"):
                self.coordinates[line.split("const loc_")[1].split(" ")[0]] = parse_js_object(line)

    def parse(self, response):
        for location in response.xpath('.//div[@class="venue-modal-container"]'):
            item = Feature()
            item["ref"] = location.xpath("../@class").get().split("-")[-1]
            item["lat"] = self.coordinates[item["ref"]]["lat"]
            item["lon"] = self.coordinates[item["ref"]]["lng"]
            item["branch"] = location.xpath(".//h1/text()").get().strip().replace("Burger King - ", "")
            item["addr_full"] = clean_address(
                location.xpath('.//div[@class="restaurant-modal-address"]/p/text()').get()
            )

            ways_to_order = location.xpath('string(.//div[@class="restaurant-modal-waystoorder"])').get().lower()
            apply_yes_no(Extras.DELIVERY, item, "delivery" in ways_to_order, False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "drive thru" in ways_to_order, False)

            services = location.xpath('string(.//div[@class="restaurant-modal-services"])').get().lower()
            apply_yes_no(Extras.WIFI, item, "free wifi" in services)
            apply_yes_no(Extras.KIDS_AREA, item, "play king" in services)

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                location.xpath('string(.//div[@class="restaurant-modal-dineinhours"])').get()
            )

            if drive_through_hours := location.xpath('string(.//div[@class="restaurant-modal-drivethruhours"])').get():
                oh = OpeningHours()
                oh.add_ranges_from_string(drive_through_hours)
                item["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()

            yield item
