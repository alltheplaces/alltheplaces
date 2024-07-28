from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class GoldsmithsGBSpider(Spider):
    name = "goldsmiths_gb"
    item_attributes = {"brand": "Goldsmiths", "brand_wikidata": "Q16993095"}
    start_urls = ["https://www.goldsmiths.co.uk/store-finder?q=&latitude=0&longitude=0&page=0"]

    def parse(self, response, **kwargs):
        for location in response.json()["results"]:
            location["ref"] = location.pop("name")
            location["address"]["street_address"] = clean_address(
                [location["address"].get("line1"), location["address"].get("line2")]
            )
            location["address"]["country"] = location["address"]["country"]["isocode"]
            location["phone"] = location["address"]["phone"]
            location["email"] = location["address"]["email"]

            item = DictParser.parse(location)

            item["website"] = f'https://www.goldsmiths.co.uk/store/{item["ref"]}'

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]["weekDayOpeningList"]:
                if rule["closed"]:
                    continue
                item["opening_hours"].add_range(
                    rule["weekDay"],
                    rule["openingTime"]["formattedHour"],
                    rule["closingTime"]["formattedHour"],
                    time_format="%I:%M %p",
                )

            yield item

        current_page = response.json()["pagination"]["currentPage"]
        pages = response.json()["pagination"]["numberOfPages"]
        if current_page < pages:
            yield JsonRequest(
                url=f"https://www.goldsmiths.co.uk/store-finder?q=&latitude=0&longitude=0&page={current_page + 1}"
            )
