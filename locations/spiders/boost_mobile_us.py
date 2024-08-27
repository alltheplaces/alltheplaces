from urllib.parse import urljoin

import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature


class BoostMobileUSSpider(scrapy.Spider):
    name = "boost_mobile_us"
    item_attributes = {
        "brand": "Boost Mobile",
        "brand_wikidata": "Q4943790",
    }

    def start_requests(self):
        for lat, lon in point_locations("us_centroids_50mile_radius.csv"):
            yield scrapy.Request(
                "https://www.boostmobile.com/locations/api/get-nearby-business/?lat={}&lon={}&showall=false".format(
                    lat, lon
                )
            )

    def parse(self, response):
        data = response.json()["business_list"]
        for poi in data["object_list"]:
            if poi["business_type_text"] == "National Retailer":
                # Exclude Boost Mobile inside Walmart and 7-Eleven.
                # TODO: we might want to include these in the future with located_in tags.
                continue
            item = DictParser.parse(poi)
            item["name"] = None
            item["ref"] = poi["dl2_click_id"]
            item["state"] = poi["locale"]["region"]["state"]
            item["addr_full"] = poi["address_text"]
            item["website"] = urljoin("https://www.boostmobile.com/", poi["business_link"])
            item["postcode"] = poi["address_postcode"]
            item["phone"] = poi["contact_context"]["business_phone_raw"]
            self.parse_hours(item, poi)
            yield item

        if next_page := data["next_page_number"]:
            yield scrapy.Request(response.url + f"&page={next_page}")

    def parse_hours(self, item: Feature, poi: dict):
        if hours := poi.get("all_opening_hours", {}).get("schemaHrs"):
            oh = OpeningHours()
            for h in hours:
                day, open_close = h.split(" ")
                open, close = open_close.split("-")
                oh.add_range(day, open, close)
            item["opening_hours"] = oh
