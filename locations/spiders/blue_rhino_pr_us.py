from scrapy import Spider
from scrapy.http import JsonRequest

from locations.geo import country_iseadgg_centroids
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BlueRhinoPRUSSpider(Spider):
    name = "blue_rhino_pr_us"
    item_attributes = {
        "brand": "Blue Rhino",
        "brand_wikidata": "Q65681213",
    }
    allowed_domains = ["bluerhino.com"]
    download_delay = 0.2

    def start_requests(self):
        # API only appears to support <=5 mile search radiuses, which renders
        # this spider fairly useless due to the huge number of API calls
        # required to search all of US and PR combined.
        for lat, lon in country_iseadgg_centroids(["US", "PR"], 24):
            yield JsonRequest(
                url=f"https://bluerhino.com/api/propane/GetRetailersNearPoint?latitude={lat}&longitude={lon}&radius=15&name=&type=&top=100000&cache=false"
            )

    def parse(self, response):
        locations = response.json()["Data"]

        # A maximum of 10 locations are returned at once. The search radius is
        # set to avoid receiving 10 locations in a single response. If 10
        # locations were to be returned, it is a sign that some locations have
        # most likely been truncated.
        if len(locations) >= 10:
            raise RuntimeError(
                "Locations have probably been truncated due to 10 (or more) locations being returned by a single geographic radius search, and the API restricts responses to 10 results only. Use a smaller search radius."
            )

        if len(locations) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for row in locations:
            properties = {
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "ref": row["RetailKey"],
                "located_in": row["RetailName"],
                "street_address": merge_address_lines([row["Address1"], row["Address2"], row["Address3"]]),
                "city": row["City"],
                "state": row["State"],
                "postcode": row["Zip"],
                "country": row["Country"],
                "phone": row["Phone"],
                "extras": {"check_date": row["LastDeliveryDate"].split("T", 1)[0]},
            }
            if properties["state"] == "PR":
                properties["country"] = properties.pop("state")
            if fax_number := row["Fax"].strip():
                properties["extras"]["fax"] = fax_number
            yield Feature(**properties)
