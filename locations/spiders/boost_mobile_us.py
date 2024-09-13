from typing import Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BoostMobileUSSpider(Spider):
    name = "boost_mobile_us"
    item_attributes = {
        "brand": "Boost Mobile",
        "brand_wikidata": "Q4943790",
    }

    def start_requests(self) -> Iterable[Request]:
        for lat, lon in country_iseadgg_centroids(["US"], 79):
            yield Request(
                "https://www.boostmobile.com/locations/api/get-nearby-business/?lat={}&lon={}&showall=false".format(
                    lat, lon
                )
            )

    def parse(self, response: Response) -> Iterable[Feature | Request]:
        features = response.json()["business_list"]["object_list"]

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        for feature in features:
            if feature["business_type_text"] == "National Retailer":
                # Exclude Boost Mobile inside Walmart and 7-Eleven.
                # TODO: we might want to include these in the future with located_in tags.
                continue
            item = DictParser.parse(feature)
            item["name"] = None
            item["ref"] = feature["dl2_click_id"]
            item["city"] = feature["locale"]["name"]
            item["state"] = feature["locale"]["region"]["state"]
            item["addr_full"] = clean_address(feature["address_text_lines"])
            item["website"] = urljoin("https://www.boostmobile.com/", feature["business_link"])
            item["postcode"] = feature["address_postcode"]
            item["phone"] = feature["contact_context"]["business_phone_raw"]
            item["opening_hours"] = self.parse_opening_hours(feature)
            yield item

        if next_page := response.json()["business_list"]["next_page_number"]:
            yield Request(response.url + f"&page={next_page}")

    def parse_opening_hours(self, feature: dict) -> OpeningHours:
        oh = OpeningHours()
        if hours := feature.get("all_opening_hours", {}).get("schemaHrs"):
            for h in hours:
                day, open_close = h.split(" ")
                open, close = open_close.split("-")
                oh.add_range(day, open, close)
        return oh
