import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TacoBuenoSpider(Spider):
    name = "taco_bueno"
    item_attributes = {"brand": "Taco Bueno", "brand_wikidata": "Q7673958"}
    start_urls = ["https://locations.tacobueno.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        build_id = re.search(r"buildId\"\s*:\s*\"(.+)\",", response.text).group(1)
        yield JsonRequest(
            url=f"https://locations.tacobueno.com/_next/data/{build_id}/index.json", callback=self.parse_locations
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json()["pageProps"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = ", ".join(location["addressLines"])
            oh = OpeningHours()
            oh.add_ranges_from_string(",".join(location["formattedBusinessHours"]))
            item["opening_hours"] = oh
            yield item

    # async def start(self) -> AsyncIterator[Request]:
    #     for state in GeonamesCache().get_us_states():
    #         yield Request(f"https://buenoonthego.com/mp/ndXTAL/searchByStateCode_JSON?stateCode='{state}'")
    #
    # @staticmethod
    # def convert_hours(times: dict) -> OpeningHours:
    #     if times == "Closed":
    #         return
    #     oh = OpeningHours()
    #     start_time, end_time = times.split(" - ")
    #     oh.add_days_range(DAYS, start_time, end_time, time_format="%I:%M %p")
    #     return oh
    #
    # def parse(self, response):
    #     results = response.json()
    #     if results:
    #         for i in results:
    #             ref = i["storeid"]
    #             name = i["restaurantname"]
    #             street = clean_address([i["address1"], i["address2"], i["address3"]])
    #             city = i["city"]
    #             state = i["statecode"]
    #             postcode = i["zipcode"]
    #             country = i["country"]
    #             phone = i["phone"]
    #             lon = i["longitude"]
    #             lat = i["latitude"]
    #             # business_hours seems to hold bad data
    #             hours = self.convert_hours(i["businesshours"])
    #             yield Feature(
    #                 ref=ref,
    #                 name=name,
    #                 street_address=street,
    #                 city=city,
    #                 state=state,
    #                 postcode=postcode,
    #                 country=country,
    #                 phone=phone,
    #                 lon=lon,
    #                 lat=lat,
    #                 opening_hours=hours,
    #             )
