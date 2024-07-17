import json

from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class HaysTravelGBSpider(Spider):
    name = "hays_travel_gb"
    item_attributes = {"brand": "Hays Travel", "brand_wikidata": "Q70250954"}
    start_urls = ["       https://branches.haystravel.co.uk/api/branches"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        items = response.json()["data"]

        for location in items:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["name"]
            item["street_address"] = location["address"]
            item["city"] = location["name"]
            item["postcode"] = location["postcode"]
            item["website"] = urljoin("https://www.haystravel.co.uk/branches/", location["name"])
            item["phone"] = location["phone"]
            item["email"] = location["email"]

          #  item["opening_hours"] = OpeningHours()
          #  for day in map(str.lower, DAYS_FULL):
          #      item["Opening_hours"]=day
          #      item["opening_hours"].add_ranges_from_string(
          #          location["{}_hours".format(day)], delimiters=[" - "]
          #      )

            yield item
