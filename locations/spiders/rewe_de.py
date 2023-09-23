from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class REWEDESpider(Spider):
    name = "rewe_de"
    item_attributes = {"brand": "REWE", "brand_wikidata": "Q16968817"}
    allowed_domains = ["mobile-api.rewe.de"]
    requires_proxy = True  # Cloudflare bot blocking is in use
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for lat, lon in point_locations("de_centroids_iseadgg_50km_radius.csv"):
            yield JsonRequest(
                url=f"https://mobile-api.rewe.de/api/v3/market/search?latitude={lat}&longitude={lon}&distance=50",
                callback=self.parse_search_results,
            )

    def parse_search_results(self, response):
        for location in response.json()["markets"]:
            market_id = location["id"]
            yield JsonRequest(
                url=f"https://mobile-api.rewe.de/api/v3/market/details?marketId={market_id}",
                callback=self.parse_location,
            )

    def parse_location(self, response):
        item = DictParser.parse(response.json()["marketItem"])
        hours_string = ""
        for day_hours in response.json()["openingTimes"]:
            day_range = day_hours["days"]
            hours_range = day_hours["hours"]
            hours_string = f"{hours_string} {day_range}: {hours_range}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
