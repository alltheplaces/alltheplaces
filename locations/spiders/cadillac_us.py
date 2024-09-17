from scrapy import Request, Spider

from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class CadillacUSSpider(Spider):
    name = "cadillac_us"
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
        for lat, lon in country_iseadgg_centroids(["US"], 158):
            yield Request(
                url=f"https://www.cadillac.com/bypass/pcf/quantum-dealer-locator/v1/getDealers?desiredCount=1000&distance=100&makeCodes=006&latitude={lat}&longitude={lon}&searchType=latLongSearch",
                headers=headers,
            )

    def parse(self, response):
        locations = response.json().get("payload", {}).get("dealers")

        # A maximum of 50 locations are returned at once. The search radius is
        # set to avoid receiving 50 locations in a single response. If 50
        # locations were to be returned, it is a sign that some locations have
        # most likely been truncated.
        if len(locations) >= 50:
            raise RuntimeError(
                "Locations have probably been truncated due to 50 (or more) locations being returned by a single geographic radius search, and the API restricts responses to 50 results only. Use a smaller search radius."
            )

        if len(locations) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for data in locations:
            item = Feature()
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
