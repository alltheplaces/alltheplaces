import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BuffaloWildWingsUSSpider(Spider):
    name = "buffalo_wild_wings_us"
    item_attributes = {"brand": "Buffalo Wild Wings", "brand_wikidata": "Q509255"}
    allowed_domains = ["buffalowildwings.com"]
    start_urls = [
        "https://api-idp.buffalowildwings.com/bww/web-exp-api/v1/location?latitude=44.97&longitude=-103.77&radius=100000&limit=100&page=0&locale=en-us"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, meta={"page": 0}, dont_filter=True)

    def parse(self, response):
        for location in response.json()["locations"]:
            if location["isClosed"]:
                continue

            item = DictParser.parse(location)
            item["ref"] = location["metadata"]["restaurantNumber"]
            item["lat"] = location["details"]["latitude"]
            item["lon"] = location["details"]["longitude"]
            item["street_address"] = clean_address(
                [
                    location["contactDetails"]["address"]["line1"],
                    location["contactDetails"]["address"]["line2"],
                    location["contactDetails"]["address"]["line3"],
                ]
            )
            item["city"] = location["contactDetails"]["address"]["city"]
            item["state"] = location["contactDetails"]["address"]["stateProvinceCode"]
            item["postcode"] = location["contactDetails"]["address"]["postalCode"]
            item["phone"] = location["contactDetails"]["phone"]
            item["website"] = "https://www.buffalowildwings.com/locations/" + location["url"]

            for service in location["services"]:
                if service["type"] == "STORE":
                    item["opening_hours"] = OpeningHours()
                    for day_hours in service["hours"]:
                        if day_hours["isTwentyFourHourService"]:
                            item["opening_hours"].add_range(day_hours["dayOfWeek"].title(), "00:00", "23:59")
                        else:
                            item["opening_hours"].add_range(
                                day_hours["dayOfWeek"].title(), day_hours["startTime"], day_hours["endTime"]
                            )

            yield item

        if not response.json()["metadata"]["isLastPage"]:
            next_page = response.meta["page"] + 1
            new_url = re.sub(r"&page=\d+", f"&page={next_page}", response.url)
            yield JsonRequest(url=new_url, meta={"page": next_page}, dont_filter=True)
