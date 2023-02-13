from scrapy import Spider

from locations.dict_parser import DictParser


class DaveAndBustersSpider(Spider):
    name = "dave_and_busters"
    item_attributes = {"brand": "Dave and Busters", "brand_wikidata": "Q5228205"}
    start_urls = ["https://www.daveandbusters.com/bin/courses.json?mode=location"]

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            if not location["websiteUrl"]:
                continue  # "Test" entry

            location["address"]["street_address"] = ", ".join(
                filter(None, [location["address"].pop("line1"), location["address"].pop("line2")])
            )
            location["website"] = location.pop("websiteUrl")

            yield DictParser.parse(location)
