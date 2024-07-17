from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature


class HaysTravelGBSpider(Spider):
    name = "hays_travel_gb"
    item_attributes = {"brand": "Hays Travel", "brand_wikidata": "Q70250954"}
    start_urls = ["       https://branches.haystravel.co.uk/api/branches"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        print(data["data"])
        items = data["data"]

        for location in items:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["name"]
            item["street_address"] = location["address"]
            item["city"] = location["name"]
            item["postcode"] = location["postcode"]
            item["website"] = urljoin("https://www.americangolf.co.uk/stores?store=", location["ID"])
            item["phone"] = location["phone"]
            item["email"] = location["email"]

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                item["opening_hours"].add_range(
                    day,
                    location["{}_hours".format(day)].strip(),
                )

            yield item
