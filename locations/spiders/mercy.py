import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MercySpider(scrapy.Spider):
    name = "mercy"
    item_attributes = {"brand": "Mercy", "brand_wikidata": "Q30289045"}
    allowed_domains = ["mercy.net"]
    start_urls = [
        "https://www.mercy.net/content/mercy/us/en.solrQueryhandler?q=*:*&solrsort=&latitude=38.627002&longitude=-90.199404&start=0&rows=10&locationType=&locationOfferings=&servicesOffered=&distance=9999&noResultsSuggestions=true&pagePath=%2Fsearch%2Flocation"
    ]

    def parse(self, response):
        number_locations = response.json().get("numFound")
        url = f"https://www.mercy.net/content/mercy/us/en.solrQueryhandler?q=*:*&solrsort=&latitude=38.627002&longitude=-90.199404&start=0&rows={number_locations}&locationType=&locationOfferings=&servicesOffered=&distance=9999&noResultsSuggestions=true&pagePath=/search/location"
        yield scrapy.Request(url=url, callback=self.parse_location)

    def parse_location(self, response):
        for data in response.json().get("docs"):
            item = DictParser.parse(data)
            item["lat"] = data.get("location_0_coordinate")
            item["lon"] = data.get("location_1_coordinate")
            item["name"] = data.get("jcr_title")
            item["street_address"] = item.pop("addr_full")
            item["website"] = f'https://www.{self.allowed_domains[0]}{data.get("url")}'
            item["ref"] = f'https://www.{self.allowed_domains[0]}{data.get("id")}'

            oh = OpeningHours()
            if data.get("operationHours"):
                for day, value in json.loads(data.get("operationHours")[0]).items():
                    if value.get("status") == "Closed":
                        continue
                    for helfday in value.get("hours"):
                        oh.add_range(
                            day=day,
                            open_time=helfday.get("start"),
                            close_time=helfday.get("end"),
                        )

            item["opening_hours"] = oh.as_opening_hours()

            yield item
