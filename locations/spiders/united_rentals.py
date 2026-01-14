from scrapy import Spider

from locations.dict_parser import DictParser


class UnitedRentalsSpider(Spider):
    name = "united_rentals"
    item_attributes = {"brand": "United Rentals", "brand_wikidata": "Q7889101"}
    start_urls = ["https://www.unitedrentals.com/api/v4/locations"]

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)

            # The URL in the response is relative
            item["website"] = response.urljoin(location["url"])

            # The public "branch ID" is found at the end of the URL
            item["ref"] = item["branch"] = location["url"].split("/")[-1].upper()

            # The "name" key in the response is the facility type
            item["name"] = "United Rentals"

            # The opening hours can be found on the branch webpage, but it's not really worth scraping

            yield item
