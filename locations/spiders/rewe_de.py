import re

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

    @staticmethod
    def clean_url_text(text: str) -> str:
        text = (
            text.lower()
            .replace(".", "")
            .replace("/", "-")
            .replace(" ", "-")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ä", "ae")
            .replace("ß", "ss")
        )
        text = re.sub(r"-+", "-", text)
        return text

    def parse_location(self, response):
        location = response.json()["marketItem"]
        item = DictParser.parse(location)
        item.pop("street_address", None)
        item["addr_full"] = ", ".join(filter(None, [location.get("addressLine1"), location.get("addressLine2")]))
        item["city"] = location["rawValues"].get("city")
        item["postcode"] = location["rawValues"].get("postalCode")
        if item.get("city") and location.get("addressLine1"):
            item["website"] = (
                "https://www.rewe.de/marktseite/"
                + self.clean_url_text(item["city"])
                + "/"
                + location["id"]
                + "/rewe-markt-"
                + self.clean_url_text(location["addressLine1"])
                + "/"
            )
        item["phone"] = response.json().get("phone")
        hours_string = ""
        for day_hours in response.json()["openingTimes"]:
            day_range = day_hours["days"]
            hours_range = day_hours["hours"]
            hours_string = f"{hours_string} {day_range}: {hours_range}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
