from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class DaveAndBustersSpider(Spider):
    name = "dave_and_busters"
    item_attributes = {"brand": "Dave and Busters", "brand_wikidata": "Q5228205"}
    allowed_domains = ["www.daveandbusters.com"]
    start_urls = ["https://www.daveandbusters.com/content/dnb-request/datadetails.json?mode=location"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        # Returned JSON object is malformed
        for location in parse_js_object(response.text)["locations"]:
            if location["isComingSoon"]:
                continue
            if "COMING SOON" in location["name"].upper():
                continue

            location["address"]["street_address"] = clean_address(
                [location["address"].pop("line1"), location["address"].pop("line2")]
            )
            location["website"] = location.pop("websiteUrl")

            yield DictParser.parse(location)
