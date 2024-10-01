import re

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Extras, apply_yes_no
from locations.geo import city_locations
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


# Also used by DO, FJ, HU, PY
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

            if title := location.xpath('div[@class="bk-title"]/text()').get():
                item["branch"] = title
            else:
                item["branch"] = item["street_address"]

            if item["ref"] is None:
                item["ref"] = item["branch"].lower().replace(" ", "-")

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
            for day in DAYS_3_LETTERS:
                if times := response.xpath(f'.//div[@class="bk-location_{day.lower()}_dining"]/text()').get():
                    times = re.sub(r"\d\d\d\d-\d\d-\d\d ", "", times)
                    times = "-".join([time for time in times.split(";") if time != "0"])
                    item["opening_hours"].add_ranges_from_string(f"{day} {times}")

            drive_through = location.xpath('div[@class="bk-dt-lane-type"]/text()').get() in ["Single Lane"]
            apply_yes_no(Extras.WIFI, item, location.xpath('div[@class="bk-wifi-supported"]/text()').get() == "1")
            apply_yes_no(
                Extras.KIDS_AREA, item, location.xpath('div[@class="bk-playground-type"]/text()').get() == "Yes"
            )
            apply_yes_no(Extras.DRIVE_THROUGH, item, drive_through)

            if drive_through:
                o = OpeningHours()
                for day in DAYS_3_LETTERS:
                    if times := response.xpath(f'.//div[@class="bk-location_{day.lower()}_drivethru"]/text()').get():
                        times = re.sub(r"\d\d\d\d-\d\d-\d\d ", "", times)
                        times = "-".join([time for time in times.split(";") if time != "0"])
                        o.add_ranges_from_string(f"{day} {times}")
                item["extras"]["opening_hours:drive_through"] = o.as_opening_hours()

            yield item
        if next_page := response.xpath('//li[contains(@class, "pager-next")]/a/@href').get():
            yield Request(url=self.host + next_page, callback=self.parse)
