import scrapy

from locations.hours import DAYS_FR, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class AmericanVintageSpider(JSONBlobSpider):
    name = "american_vintage"
    item_attributes = {"brand": "American Vintage", "brand_wikidata": "Q2422884"}
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for country in [
            "AT",
            "BE",
            "CH",
            "CN",
            "CZ",
            "DE",
            "DK",
            "EE",
            "ES",
            "FR",
            "GB",
            "HK",
            "IE",
            "IT",
            "LU",
            "NL",
            "PT",
            "US",
        ]:
            url = f"https://www.americanvintage-store.com/on/demandware.store/Sites-AMV-Site/fr_FR/Stores-FindStores?countryCode={country}"
            yield scrapy.Request(url)

    def post_process_item(self, item, response, location):
        item["opening_hours"] = oh = OpeningHours()
        for r in location.get("scheduleHours", []):
            if not r["isClosed"]:
                periods = r["openingHours"].split(" / ")
                for period in periods:
                    hours = period.split("-")
                    oh.add_range(DAYS_FR[r["day"].title()], hours[0].strip(), hours[1].strip())
        yield item
