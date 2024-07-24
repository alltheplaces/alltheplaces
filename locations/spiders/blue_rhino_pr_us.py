from scrapy import Spider
from scrapy.http import JsonRequest

from locations.geo import point_locations
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BlueRhinoPRUSSpider(Spider):
    name = "blue_rhino_pr_us"
    item_attributes = {
        "brand": "Blue Rhino",
        "brand_wikidata": "Q65681213",
    }
    allowed_domains = ["bluerhino.com"]

    def start_requests(self):
        # The server times out at a 500km search radius, so use 200km instead.
        for lat, lon in point_locations("pr_us_centroids_iseadgg_175km_radius.csv"):
            yield JsonRequest(
                url=f"https://bluerhino.com/api/propane/GetRetailersNearPoint?latitude={lat}&longitude={lon}&radius=200&name=&type=&top=100000&cache=false"
            )

    def parse(self, response):
        for row in response.json()["Data"]:
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
