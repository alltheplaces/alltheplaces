import json
import re

from scrapy import FormRequest, Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.pipelines.address_clean_up import clean_address


class NextSpider(Spider):
    name = "next"
    NEXT = {"brand": "Next", "brand_wikidata": "Q246655"}
    NEXT_HOME = {"brand": "Next Home", "brand_wikidata": "Q116897680"}
    VICTORIAS_SECRET = {"brand": "Victoria's Secret", "brand_wikidata": "Q332477"}
    PINK = {"brand": "Pink", "brand_wikidata": "Q20716793"}
    item_attributes = NEXT
    start_urls = ["https://www.next.co.uk/countryselect"]
    handle_httpstatus_all = True

    @staticmethod
    def get_time(time: str) -> str:
        if len(time) == 3:
            return time.zfill(4)
        elif len(time) == 4:
            return time

    def store_hours(self, store: dict) -> OpeningHours:
        o = OpeningHours()

        for day in ["mon", "tues", "weds", "thurs", "fri", "sat", "sun"]:
            open_time = self.get_time(store[f"{day}_open"])
            close_time = self.get_time(store[f"{day}_close"])
            if open_time and close_time:
                o.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H%M",
                )

        return o

    def parse(self, response, **kwargs):
        for country in response.xpath('//*[contains(@class, "country-name")]/text()').getall():
            yield FormRequest(
                url="https://stores.next.co.uk/index/stores",
                formdata={"country": country.strip()},
                callback=self.parse_country,
            )

    def parse_country(self, response, **kwargs):
        for city in response.xpath("//option/@value").getall():
            yield Request(url=f"https://stores.next.co.uk/stores/single/{city}", callback=self.parse_location)

    def parse_location(self, response, **kwargs):
        if data := response.xpath('//script[contains(.,"window.lctr.single_search")]/text()').re_first(
            r"window\.lctr\.results\.push\(({.+})\)"
        ):
            location = json.loads(data)
            location["street_address"] = clean_address(
                [
                    # Fields aren't descriptive of contents
                    location.pop("AddressLine"),
                    location.pop("centre"),
                    location.pop("street"),
                    location.pop("town"),
                ]
            )
            item = DictParser.parse(location)
            item["ref"] = location["location_id"]
            item["branch"] = item.pop("name")
            item["website"] = response.url

            item["opening_hours"] = self.store_hours(location)

            if location["home_store"] == "home_store":
                item.update(self.NEXT_HOME)
            elif re.search(r"Victoria'?s Secret", location["branch_name"]):
                if "PINK" in location["branch_name"]:
                    item.update(self.PINK)
                else:
                    item.update(self.VICTORIAS_SECRET)
            # else normal store

            if "phone" in item and item["phone"] is not None:
                if item["phone"].replace(" ", "").startswith("+443"):
                    item.pop("phone", None)
            yield item
        elif data := response.xpath('//script[@type="application/ld+json"]/text()').get():
            location = json.loads(data)
            item = LinkedDataParser.parse_ld(location)
            item["ref"] = location["url"].split("/")[-1]
            item["branch"] = item.pop("name")
            item["street_address"] = location["address"]["streetAddress"]
            item["city"] = location["address"]["addressLocality"]
            item["postcode"] = location["address"]["postalCode"]
            item["country"] = location["address"]["addressCountry"]
            coords = (
                response.xpath('//script[contains(.,"storeLocator.mapSelectedStore")]/text()')
                .re_first(r"storeLocator\.mapSelectedStore\((.+)\)")
                .split(",")
            )
            item["lat"] = coords[-2]
            item["lon"] = coords[-1]
            oh = OpeningHours()
            for opening_hour in location["openingHoursSpecification"]:
                if "opens" in opening_hour:
                    if "Closed" not in opening_hour:
                        oh.add_range(
                            DAYS_EN[opening_hour["dayOfWeek"]],
                            opening_hour["opens"][0:5],
                            opening_hour["closes"][0:5],
                        )
                        item["opening_hours"] = oh
            if re.search(r"Victoria'?s Secret", item["branch"]):
                if "PINK" in item["branch"]:
                    item.update(self.PINK)
                else:
                    item.update(self.VICTORIAS_SECRET)
            # else normal store

            yield item
