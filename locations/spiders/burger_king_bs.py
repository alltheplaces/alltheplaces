from scrapy import Spider
from scrapy.http import Request

from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingBSSpider(Spider):
    name = "burger_king_bs"
    allowed_domains = ["www.burgerking.bs"]
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    host = "https://www.burgerking.bs"
    country_code = "BS"

    def start_requests(self):
        for city in city_locations(self.country_code):
            yield Request(
                url=f"{self.host}/locations?field_geofield_distance[origin][lat]={city['latitude']}&field_geofield_distance[origin][lon]={city['longitude']}",
                callback=self.parse,
            )

    def parse(self, response):
        for location in response.xpath('//div[@class="bk-restaurants"]/ul/li'):
            item = Feature()
            item["ref"] = location.xpath('div[@class="bk-id"]/text()').get()
            item["street_address"] = location.xpath('div[@class="bk-address1"]/text()').get()
            item["branch"] = item["street_address"]
            item["city"] = location.xpath('div[@class="bk-city"]/text()').get()
            item["postcode"] = location.xpath('div[@class="bk-zip"]/text()').get()
            item["country"] = location.xpath('div[@class="bk-country"]/text()').get()
            item["phone"] = location.xpath('div[@class="bk-phone"]/text()').get()
            item["lat"] = location.xpath('div[@class="bk-latitude"]/text()').get()
            item["lon"] = location.xpath('div[@class="bk-longitude"]/text()').get()

            item["opening_hours"] = OpeningHours()
            if weekday_hours := location.xpath('div[@class="bk-weekday-hours"]/text()').get():
                item["opening_hours"].add_ranges_from_string("Mo-Fr " + weekday_hours)
            if weekend_hours := location.xpath('div[@class="bk-weekend-hours"]/text()').get():
                item["opening_hours"].add_ranges_from_string("Sa-Su " + weekend_hours)

            yield item
        if next_page := response.xpath('//li[contains(@class, "pager-next")]/a/@href').get():
            yield Request(url=self.host + next_page, callback=self.parse)
