import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

class SupercutsSpider(scrapy.Spider):
    name = "supercuts"
    item_attributes = {"brand": "Supercuts", "brand_wikidata": "Q7643239"}
    allowed_domains = ["api.regiscorp.com",]

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://api.regiscorp.com/sis/api/salon/get-states-by-brand?brand=sc",
            callback=self.parse_index,
        )

    def parse_index(self, response):
        for country in response.json().values():
            for state in country:
                st = state["state_abbreviation"].lower()
                yield scrapy.http.JsonRequest(
                    "https://api.regiscorp.com/sis/api/salon/search-by-location?brand=sc&state={}".format(st),
                    callback=self.parse_state,
                )

    def parse_state(self, response):
        for salon in response.json():
            yield scrapy.Request(url ="https://api.regiscorp.com/sis/api/salon?salon-number={}".format(int(salon['salonId'])),
                callback=self.parse_salon,
            )

    def parse_salon(self, response):
        data = response.json()
        item = DictParser.parse(data)
        item["ref"] = data["salon_number"]
        item["branch"] = item.pop("name").replace(str(data["salon_number"])+"-","").replace(str(data["salon_number"])+" - ","")
        item["street"] = data["address2"]
        item["website"] = data["booking_url"]
        item["opening_hours"] = OpeningHours()
        for day,time in data["store_hours"].items():
            day = day
            open_time = time["open"]
            close_time = time["close"]
            item["opening_hours"].add_range(day=day,open_time=open_time,close_time=close_time,time_format= "%I:%M %p")
        yield item
