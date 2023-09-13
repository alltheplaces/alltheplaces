import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CueSpider(Spider):
    name = "cue"
    item_attributes = {"brand": "Cue", "brand_wikidata": "Q5192554"}
    allowed_domains = ["www.cue.com"]
    start_urls = [
        "https://www.cue.com/Geolocation/GetStoresByState",
        "https://www.cue.com/GeoLocation/GetStoresByCoordinates",
    ]

    def start_requests(self):
        for url in self.start_urls:
            if "GetStoresByState" in url:
                for state_code in ["ACT", "NSW", "QLD", "SA", "TAS", "VIC", "WA"]:  # No stores in NT
                    yield JsonRequest(url=url, method="POST", data={"code": state_code})
            elif "GetStoresByCoordinates" in url:
                yield JsonRequest(
                    url=url, method="POST", data={"countryCode": "NZ", "latitude": -36.85, "longitude": 174.76}
                )  # Auckland
                yield JsonRequest(
                    url=url, method="POST", data={"countryCode": "NZ", "latitude": -41.29, "longitude": 174.79}
                )  # Wellington
                yield JsonRequest(
                    url=url, method="POST", data={"countryCode": "NZ", "latitude": -43.53, "longitude": 172.63}
                )  # Christchurch

    def parse(self, response):
        cleaned_json = (
            response.text[1:-1].replace('\\"', '"').replace("\\\\r", "").replace("\\\\n", " ").replace("\\\\/", "")
        )
        locations = json.loads(cleaned_json)
        for location in locations:
            if not location["Active"]:
                continue
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(str(location["StoreHours"]))

            if postcode := item.get("postcode"):
                item["postcode"] = str(postcode)

            yield item
