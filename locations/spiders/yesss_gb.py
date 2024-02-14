from scrapy import Spider

from locations.linked_data_parser import LinkedDataParser


class YesssGBSpider(Spider):
    name = "yesss_gb"
    item_attributes = {"brand": "Yesss Electrical", "brand_wikidata": "Q91307483", "extras": {"shop": "electrical"}}
    start_urls = ["https://www.yesss.co.uk/store-finder/location-data/all"]

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            item = LinkedDataParser.parse_ld(location["ldSchema"])
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["email"] = location["email"]
            item["branch"] = location["name"]
            item["opening_hours"] = item["name"] = None

            yield item
