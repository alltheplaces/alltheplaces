import scrapy

from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours
from locations.items import GeojsonPointItem


class CadillacSpider(scrapy.Spider):
    name = "cadillac"
    item_attributes = {
        "brand": "Cadillac",
        "brand_wikidata": "Q27436",
    }
    allowed_domains = ["cadillac.com"]

    def start_requests(self):
        headers = {
            "clientapplicationid": "quantum",
            "locale": "en-US",
        }
        point_files = "us_centroids_100mile_radius_state.csv"
        for lat, lon in point_locations(point_files):
            yield scrapy.Request(
                url=f"https://www.cadillac.com/bypass/pcf/quantum-dealer-locator/v1/getDealers?desiredCount=1000&distance=1200&makeCodes=006&latitude={lat}&longitude={lon}&searchType=latLongSearch",
                headers=headers,
            )

    def parse(self, response):
        for data in response.json().get("payload", {}).get("dealers"):
            item = GeojsonPointItem()
            item["ref"] = data.get("dealerCode")
            item["name"] = data.get("dealerName")
            item["website"] = data.get("dealerUrl")
            item["phone"] = data.get("generalContact", {}).get("phone1")
            item["street_address"] = data.get("address", {}).get("addressLine1")
            item["lat"] = data.get("geolocation", {}).get("latitude")
            item["lon"] = data.get("geolocation", {}).get("longitude")
            item["postcode"] = data.get("address", {}).get("postalCode")
            item["city"] = data.get("address", {}).get("cityName")
            item["state"] = data.get("address", {}).get("countrySubdivisionCode")
            item["country"] = data.get("address", {}).get("countryIso")

            oh = OpeningHours()
            for value in data.get("generalOpeningHour"):
                for day in value.get("dayOfWeek"):
                    oh.add_range(
                        day=DAYS[day - 1],
                        open_time=value.get("openFrom"),
                        close_time=value.get("openTo"),
                        time_format="%I:%M %p",
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
