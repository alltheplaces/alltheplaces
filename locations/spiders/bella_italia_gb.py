from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BellaItaliaGBSpider(Spider):
    name = "bella_italia_gb"
    item_attributes = {"brand": "Bella Italia", "brand_wikidata": "Q4883362"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/bella"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["storeId"]
            item["lat"] = location["addressLocation"]["lat"]
            item["lon"] = location["addressLocation"]["lon"]
            item["branch"] = location["title"]
            item["street_address"] = merge_address_lines([location["addressLine1"], location["addressLine2"]])
            item["city"] = location["addressCity"]
            item["postcode"] = location["postcode"]
            slug = urljoin(location["city"], "/", location["slug"])
            item["website"] = urljoin("https://www.bellaitalia.co.uk/restaurants/", slug)
            item["phone"] = location["phoneNumber"]
            item["email"] = location["email"]
            if location["hours"]:
                item["opening_hours"] = OpeningHours()
                for day in map(str.lower, DAYS_FULL):
                    item["opening_hours"].add_range(
                        day,
                        location["hours"]["{}Open".format(day)].strip(),
                        location["hours"]["{}Close".format(day)].strip(),
                    )

            yield item
