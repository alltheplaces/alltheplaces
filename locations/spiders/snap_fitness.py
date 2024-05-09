from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import clean_facebook, clean_instagram


class SnapFitnessSpider(Spider):
    name = "snap_fitness"
    item_attributes = {"brand": "Snap Fitness", "brand_wikidata": "Q7547254"}
    allowed_domains = ["www.snapfitness.com"]
    country_codes = [
        "ae",
        "au",
        "be",
        "ca",
        "es",
        "hk",
        "id",
        "ie",
        "mx",
        "nl",
        "nz",
        "ph",
        "sa_en",
        "sg",
        "tr",
        "tw",
        "uk",
        "us",
    ]

    def start_requests(self):
        for country_code in self.country_codes:
            yield JsonRequest(url=f"https://www.snapfitness.com/{country_code}/api/location-finder-edge")

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location.get("customProperties", {}).get("contactDetails", {}))
            item["ref"] = location["id"]
            item["name"] = location["name"]
            item["lat"] = location["customProperties"]["latitude"]
            item["lon"] = location["customProperties"]["longitude"]
            item["street_address"] = clean_address(
                [
                    location["customProperties"]["contactDetails"].get("address"),
                    location["customProperties"]["contactDetails"].get("address2"),
                ]
            )
            item["website"] = response.url.replace("/api/location-finder-edge", location["urlPath"])
            if not item.get("extras"):
                item["extras"] = {}
            item["extras"]["contact:instagram"] = clean_instagram(
                location["customProperties"]["contactDetails"].get("instagramUrl", "")
            )
            item["facebook"] = clean_facebook(location["customProperties"]["contactDetails"].get("facebookUrl", ""))
            if location["customProperties"]["contactDetails"].get("open24Hours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            yield item
