import re
from datetime import datetime
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import SocialMedia, set_closed, set_social_media
from locations.pipelines.address_clean_up import merge_address_lines


class TacoBuenoSpider(Spider):
    name = "taco_bueno"
    item_attributes = {"brand": "Taco Bueno", "brand_wikidata": "Q7673958"}
    start_urls = ["https://locations.tacobueno.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://locations.tacobueno.com/_next/data/{}/index.json".format(
                re.search(r"buildId\"\s*:\s*\"(.+)\",", response.text).group(1)
            ),
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["pageProps"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = merge_address_lines(location["addressLines"])
            item["website"] = item["website"].replace("\t", "")
            item["phone"] = "; ".join(location["phoneNumbers"])

            item["opening_hours"] = self.parse_opening_hours(location["businessHours"])
            apply_category(Categories.FAST_FOOD, item)

            set_social_media(item, SocialMedia.FACEBOOK, location["attributes"].get("url_facebook"))
            item["extras"]["website:menu"] = location["attributes"]["url_order_ahead"]
            apply_yes_no(Extras.INDOOR_SEATING, item, location["attributes"]["serves_dine_in"] is True)
            apply_yes_no(Extras.TAKEAWAY, item, location["attributes"]["has_takeout"] is True)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["attributes"].get("has_drive_through") is True)
            if hours := (location.get("otherHours") or {}).get("DRIVE_THROUGH"):
                item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(hours).as_opening_hours()
            item["extras"]["start_date"] = location["openingDate"]
            if location["closingDate"]:
                set_closed(item, datetime.fromisoformat(location["closingDate"]))

            yield item

    def parse_opening_hours(self, hours: list) -> OpeningHours:
        oh = OpeningHours()
        for day, hours in zip(DAYS, hours):
            oh.add_range(day, hours[0], hours[1])
        return oh
