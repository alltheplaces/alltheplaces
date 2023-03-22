from scrapy import Spider

from locations.dict_parser import DictParser


class DaveAndBustersSpider(Spider):
    name = "dave_and_busters"
    item_attributes = {"brand": "Dave and Busters", "brand_wikidata": "Q5228205"}
    allowed_domains = ["www.daveandbusters.com"]
    start_urls = ["https://www.daveandbusters.com/content/dnb-request/datadetails.json?mode=location"]

    def parse(self, response):
        for location in response.json()["locations"]:
            if "COMING SOON" in location["name"].upper():
                continue

            location["address"]["street_address"] = ", ".join(
                filter(None, [location["address"].pop("line1"), location["address"].pop("line2")])
            )
            location["website"] = location.pop("websiteUrl")

            yield DictParser.parse(location)
