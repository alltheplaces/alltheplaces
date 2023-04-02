import json
import re

import scrapy

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MatchLUSpider(scrapy.Spider):
    name = "match_lu"
    item_attributes = {"brand": "Match", "brand_wikidata": "Q513977"}
    start_urls = ["https://www.supermarche-match.lu/storelocator?query=&type%5B%5D=match"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        stores = json.loads(response.xpath('//*[@id="map"]/@data-dna').get())
        for store in stores:
            if store["type"] == "markers":
                properties = {}

                locations = store["locations"][0]
                properties["lon"] = locations["lng"]
                properties["lat"] = locations["lat"]

                regex = '(<a href=")(.+?)(" class="cta cta--infoBulle cta--storeLink">)'
                website_str = store["options"]["infoWindowOptions"]["content"]
                properties["website"] = re.findall(regex, website_str)[0][1]
                properties["ref"] = properties["website"]
                yield scrapy.Request(
                    url=properties["website"],
                    callback=self.parse_store,
                    cb_kwargs={"properties": properties},
                )

    def parse_store(self, response, properties):
        properties["name"] = response.xpath('//*[@class="store-informations-title"]/text()').get()

        street_address, postcode_city = response.xpath('//*[@class="store-informations-address"]/text()').getall()
        postcode, city = postcode_city.strip().split(" ", maxsplit=1)
        properties["street_address"] = street_address.strip()
        properties["postcode"] = postcode
        properties["city"] = city

        properties["phone"] = response.xpath('//*[@class="link--phone"]/@href').get().replace("tel:", "")
        properties["opening_hours"] = self.parse_opening_hours(response)

        yield Feature(**properties)

    def parse_opening_hours(self, response):
        oh = OpeningHours()

        days = response.xpath('//*[@class="store-timetable-table-day"]/text()').getall()
        hours = response.xpath('//*[@class="store-timetable-table-hours"]/text()').getall()
        for day, hour in zip(days, hours):
            hour_strip = hour.strip()
            oh.add_ranges_from_string(ranges_string=day + " " + hour_strip, days=DAYS_FR)

        return oh.as_opening_hours()
