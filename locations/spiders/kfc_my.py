import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KFCMYSpider(scrapy.Spider):
    name = "kfc_my"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    allowed_domains = ["kfc.com.my"]
    start_urls = ["https://kfc.com.my/graphql"]

    def start_requests(self):
        gql_query = """query allLocation {
    allLocation {
        locations {
            address
            city
            country
            lat
            locationId
            long
            name
            phone
            selfcollect_close
            selfcollect_open
            state
            zip
            __typename
        }
        __typename
    }
}"""
        url = self.start_urls[0] + f"?query={gql_query}"
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for location in response.json()["data"]["allLocation"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["locationId"]
            oh = OpeningHours()
            for day in DAYS:
                if len(location["selfcollect_open"].split(":")) == 2:
                    location["selfcollect_open"] = location["selfcollect_open"] + ":00"
                if len(location["selfcollect_close"].split(":")) == 2:
                    location["selfcollect_close"] = location["selfcollect_close"] + ":00"
                if location["selfcollect_close"] == "24:00:00":
                    location["selfcollect_close"] = "23:59:00"
                oh.add_range(day, location["selfcollect_open"], location["selfcollect_close"], "%H:%M:%S")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
