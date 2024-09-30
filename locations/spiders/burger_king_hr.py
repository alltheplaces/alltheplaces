from scrapy import Spider

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import DAYS_HR, OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingHRSpider(Spider):
    name = "burger_king_hr"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.hr/restorani"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath('//div[@class="marker"]'):
            item = Feature()
            item["lat"] = location.xpath(".//@data-latitude").get()
            item["lon"] = location.xpath(".//@data-longitude").get()
            item["branch"] = location.xpath('.//div[@class="name"]/text()').get()
            item["street_address"] = location.xpath('.//div[@class="address"]/text()').get()
            item["city"] = location.xpath('.//div[@class="city"]/text()').get()
            properties = location.xpath('.//div[@class="properties"]/img/@title').getall()
            apply_yes_no(Extras.WIFI, item, "Wifi" in properties)
            apply_yes_no(PaymentMethods.CARDS, item, "Kartično plaćanje" in properties)
            apply_yes_no(Extras.DELIVERY, item, "Dostava" in properties)

            if hours := location.xpath('string(.//div[@class="working-hours"])').get():
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours, days=DAYS_HR)

            yield item
