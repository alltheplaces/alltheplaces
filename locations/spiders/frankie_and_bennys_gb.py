from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FrankieAndBennysGBSpider(Spider):
    name = "frankie_and_bennys_gb"
    item_attributes = {"brand": "Frankie & Benny's", "brand_wikidata": "Q5490892"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/frankies"]

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
            item["phone"] = location["phoneNumber"]
            item["email"] = location["email"]

            if location.get("hours"):
                item["opening_hours"] = OpeningHours()
                for day in map(str.lower, DAYS_FULL):
                    item["opening_hours"].add_range(
                        day,
                        location["hours"]["{}Open".format(day)].strip(),
                        location["hours"]["{}Close".format(day)].strip(),
                    )

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = urljoin("https://www.frankieandbennys.com/restaurants/", location["slug"])
        yield item
