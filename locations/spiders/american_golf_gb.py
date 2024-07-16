from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AmericanGolfGBSpider(Spider):
    name = "american_golf_gb"
    item_attributes = {"brand": "American Golf", "brand_wikidata": "Q62657494"}
    start_urls = [
        "https://www.americangolf.co.uk/on/demandware.store/Sites-AmericanGolf-GB-Site/en_GB/Stores-GetAllStores"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["ID"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["name"]
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["city"] = location["city"]
            item["postcode"] = location["postalCode"]
            item["website"] = urljoin("https://www.americangolf.co.uk/stores?store=", location["ID"])
            item["phone"] = location["phone"]
            item["email"] = location["email"]

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                item["opening_hours"].add_range(
                    day,
                    location["storeHours"]["{}".format(day)].strip(),
                )

            yield item
