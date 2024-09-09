from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT

class AmericanGolfGBSpider(Spider):
    name = "american_golf_gb"
    item_attributes = {"brand": "American Golf", "brand_wikidata": "Q62657494"}
    start_urls = [
        "https://www.americangolf.co.uk/on/demandware.store/Sites-AmericanGolf-GB-Site/en_GB/Stores-GetAllStores"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = Feature()
            item["ref"] = location["ID"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["name"]
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["city"] = location["city"]
            item["postcode"] = location["postalCode"]
            url='/stores?store='+location["ID"]
            item["website"] = urljoin('https://www.americangolf.co.uk',url)
            item["phone"] = location["phone"]
            item["email"] = location["email"]

            if location.get("storeHours"):
               item["opening_hours"] = OpeningHours()
               for day in map(str.lower, DAYS_FULL):
                   day_hours=location["storeHours"][format(day)].strip()
                   if "CLOSED" in day_hours.upper():
                       continue
                   item["opening_hours"].add_range(
                       day,
                       day_hours.split(" - ", 1)[0], day_hours.split(" - ", 1)[1]
                   )
            yield item
